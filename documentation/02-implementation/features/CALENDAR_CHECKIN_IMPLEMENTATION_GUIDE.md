# Calendar Check-in System Implementation Guide

## Overview

This document provides a comprehensive guide to implementing a persistent calendar check-in system that allows users to:
1. Add routine plan items to a calendar
2. Check-in completed tasks
3. Persist check-in status across page refreshes and server restarts
4. Sync check-in status manually via UI buttons

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   Database      │
│                 │    │                  │    │                 │
│ Routine Plan    │───▶│ Calendar API     │───▶│ plan_items      │
│ Calendar Tabs   │    │ Engagement API   │    │ task_checkins   │
│                 │    │                  │    │ calendar_sel... │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Backend Implementation

### 1. Database Schema

#### Core Tables

**plan_items**: Stores extracted tasks from AI-generated plans
```sql
CREATE TABLE IF NOT EXISTS plan_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_result_id UUID NOT NULL,
    profile_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    scheduled_time TIME,
    scheduled_end_time TIME,
    estimated_duration_minutes INTEGER,
    task_type VARCHAR(50),
    priority_level INTEGER,
    time_block TEXT,
    time_block_id UUID,
    plan_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**task_checkins**: Stores completion status for tasks
```sql
CREATE TABLE IF NOT EXISTS task_checkins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id TEXT NOT NULL,
    plan_item_id UUID NOT NULL,
    analysis_result_id UUID NOT NULL,
    completion_status VARCHAR(20) NOT NULL CHECK (completion_status IN ('completed', 'partial', 'skipped')),
    completed_at TIMESTAMP WITH TIME ZONE,
    satisfaction_rating INTEGER CHECK (satisfaction_rating BETWEEN 1 AND 5),
    planned_date DATE NOT NULL,
    user_notes TEXT,
    
    -- Prevent duplicate check-ins
    UNIQUE(profile_id, plan_item_id, planned_date)
);
```

**calendar_selections**: Tracks which items users added to calendar
```sql
CREATE TABLE IF NOT EXISTS calendar_selections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id TEXT NOT NULL,
    plan_item_id UUID NOT NULL,
    selected_for_calendar BOOLEAN DEFAULT TRUE,
    selection_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    calendar_notes TEXT
);
```

### 2. API Endpoints

#### Simple Check-in Status Endpoint (MVP Solution)

**GET `/api/v1/engagement/checkins/status/{profile_id}`**

```python
@router.get("/checkins/status/{profile_id}")
async def get_checkin_status(
    profile_id: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get simple check-in status for all tasks by profile_id
    
    Returns a list of all completed plan_item_ids for the user.
    Frontend can use this for simple O(1) lookup to mark items as checked.
    """
    try:
        # Simple query: get all completed tasks for this profile
        result = supabase.table("task_checkins")\
            .select("plan_item_id, completion_status")\
            .eq("profile_id", profile_id)\
            .eq("completion_status", "completed")\
            .execute()
        
        # Extract just the plan_item_ids for simple frontend lookup
        completed_plan_item_ids = [
            item["plan_item_id"] for item in (result.data or [])
        ]
        
        return {
            "profile_id": profile_id,
            "completed_plan_item_ids": completed_plan_item_ids,
            "total_completed": len(completed_plan_item_ids)
        }
        
    except Exception as e:
        logger.error(f"Error fetching check-in status for profile {profile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch check-in status: {str(e)}")
```

#### Batch Check-in Endpoint

**POST `/api/v1/engagement/batch-checkin`**

```python
@router.post("/batch-checkin")
async def submit_batch_checkin(
    request: BatchCheckinRequest,
    supabase: Client = Depends(get_supabase)
):
    """Submit multiple task check-ins at once (MVP - simple completed status only)"""
    try:
        checkin_data = []
        
        for checkin_item in request.checkins:
            # Get analysis_result_id and plan_date from plan_items table
            plan_item_result = supabase.table("plan_items")\
                .select("analysis_result_id, plan_date")\
                .eq("id", checkin_item.plan_item_id)\
                .execute()
            
            if not plan_item_result.data:
                logger.warning(f"Plan item not found: {checkin_item.plan_item_id}")
                continue
            
            analysis_result_id = plan_item_result.data[0]["analysis_result_id"]
            plan_date = plan_item_result.data[0]["plan_date"]
            
            checkin_data.append({
                'profile_id': request.profile_id,
                'plan_item_id': checkin_item.plan_item_id,
                'analysis_result_id': analysis_result_id,
                'completion_status': 'completed',
                'planned_date': plan_date,
                'completed_at': datetime.now().isoformat(),
                'actual_completion_time': datetime.now().isoformat()
            })
        
        # Batch upsert to handle updates to existing check-ins
        result = supabase.table("task_checkins")\
            .upsert(checkin_data, on_conflict="profile_id,plan_item_id,planned_date")\
            .execute()
        
        items_processed = len(result.data) if result.data else 0
        return {
            "success": True,
            "message": f"Successfully checked in {items_processed} tasks",
            "items_processed": items_processed
        }
            
    except Exception as e:
        logger.error(f"Error recording batch check-in: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to record batch check-in: {str(e)}")
```

#### Undo Check-in Endpoint

**DELETE `/api/v1/engagement/batch-checkin`**

```python
@router.delete("/batch-checkin")
async def undo_batch_checkin(
    request: BatchUndoRequest,
    supabase: Client = Depends(get_supabase)
):
    """Undo multiple task check-ins at once (MVP - simple delete)"""
    try:
        result = supabase.table("task_checkins")\
            .delete()\
            .eq("profile_id", request.profile_id)\
            .in_("plan_item_id", request.plan_item_ids)\
            .execute()
        
        items_removed = len(result.data) if result.data else 0
        return {
            "success": True,
            "message": f"Successfully undid {items_removed} check-ins",
            "items_removed": items_removed
        }
            
    except Exception as e:
        logger.error(f"Error undoing batch check-in: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to undo batch check-in: {str(e)}")
```

## Frontend Implementation

### 1. API Configuration

**api.ts** - Central API configuration
```typescript
export const API_CONFIG = {
  CALENDAR_SERVER: {
    // Priority: DEV_API_URL (localhost) > production fallback
    BASE_URL: import.meta.env.VITE_DEV_API_URL || 'https://hos-agentic-ai-prod.onrender.com',
    ENDPOINTS: {
      // Engagement endpoints
      CHECKIN_STATUS: '/api/v1/engagement/checkins/status/{profile_id}',
      BATCH_CHECKIN: '/api/v1/engagement/batch-checkin',
      // ... other endpoints
    }
  }
} as const;
```

**Environment Variables (.env)**
```env
# Calendar Development API (local testing)
VITE_DEV_API_URL=http://localhost:8002

# Cache TTL settings
VITE_CACHE_TTL_CHECKIN_STATUS=30000  # 30 seconds - check-in status needs to be fresh
```

### 2. Service Layer

**calendarService.ts** - API integration service
```typescript
class CalendarService {
  private baseUrl = `${API_CONFIG.CALENDAR_SERVER.BASE_URL}/api/calendar`;
  private engagementUrl = `${API_CONFIG.CALENDAR_SERVER.BASE_URL}/api/v1/engagement`;

  /**
   * Get simple check-in status for all tasks (MVP approach)
   * Returns a Set of completed plan_item_ids for O(1) lookup
   */
  async getCheckinStatus(profileId: string): Promise<Set<string>> {
    try {
      const response = await fetch(
        `${this.engagementUrl}/checkins/status/${profileId}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch check-in status: ${response.statusText}`);
      }

      const data = await response.json();
      const completedIds = data.completed_plan_item_ids || [];
      
      console.log(`DEBUG: getCheckinStatus - Found ${completedIds.length} completed items for profile ${profileId}`);
      
      return new Set(completedIds);
    } catch (error) {
      console.error('Error fetching check-in status:', error);
      // Return empty set on error to gracefully degrade
      return new Set();
    }
  }

  /**
   * Batch check-in tasks as completed (MVP - simple version)
   */
  async batchCheckIn(
    profileId: string, 
    planItemIds: string[],
    plannedDate: string = new Date().toISOString().split('T')[0]
  ): Promise<any> {
    try {
      const response = await fetch(`${this.engagementUrl}/batch-checkin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          profile_id: profileId,
          planned_date: plannedDate,
          checkins: planItemIds.map(id => ({
            plan_item_id: id,
            completion_status: 'completed'
          }))
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to submit batch check-in: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error submitting batch check-in:', error);
      throw this.handleApiError(error, 'Failed to check in tasks');
    }
  }

  /**
   * Undo check-in for multiple tasks (MVP - simple version)
   */
  async undoCheckIn(
    profileId: string, 
    planItemIds: string[],
    plannedDate: string = new Date().toISOString().split('T')[0]
  ): Promise<any> {
    try {
      const response = await fetch(`${this.engagementUrl}/batch-checkin`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          profile_id: profileId,
          planned_date: plannedDate,
          plan_item_ids: planItemIds
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to undo check-in: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error undoing check-in:', error);
      throw this.handleApiError(error, 'Failed to undo check-in');
    }
  }
}

export const calendarService = new CalendarService();
```

### 3. Cache Configuration

**cacheConfig.ts** - React Query configuration
```typescript
export const CACHE_TIMES = {
  // Calendar workflow cache times - reduced for more live updates
  calendarSelections: 30 * 1000, // 30 seconds - calendar selections change frequently
  availablePlanItems: 1 * 60 * 1000, // 1 minute - plan items need to be fresh
  checkinStatus: 30 * 1000, // 30 seconds - check-in status needs to be fresh
} as const;

/**
 * Query key factory for consistent cache keys
 */
export const queryKeys = {
  // Calendar workflow queries
  calendarSelections: (userId: string, date: string) => 
    ['calendarSelections', userId, date] as const,
  availablePlanItems: (userId: string, date: string, archetypeFilter?: string) => 
    archetypeFilter 
      ? ['availablePlanItems', userId, date, archetypeFilter] as const
      : ['availablePlanItems', userId, date] as const,
  checkinStatus: (userId: string) => 
    ['checkinStatus', userId] as const,
  // ... other query keys
} as const;
```

### 4. Component Implementation

#### Calendar.tsx - Main calendar component

**Key Features:**
- Simple check-in status lookup
- Batch check-in functionality
- Manual sync button
- Optimistic UI updates

```typescript
export const Calendar: React.FC<CalendarProps> = ({ userId }) => {
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [checkedInItems, setCheckedInItems] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();

  // Fetch simple check-in status for all tasks (MVP approach)
  const { data: checkinStatusSet, isLoading: checkinStatusLoading, refetch: refetchCheckinStatus } = useQuery({
    queryKey: queryKeys.checkinStatus(userId),
    queryFn: () => calendarService.getCheckinStatus(userId),
    enabled: !!userId,
    staleTime: CACHE_TIMES.checkinStatus,
  });

  // Update checked-in items state when check-in status changes (Simple MVP approach)
  useEffect(() => {
    if (checkinStatusSet) {
      setCheckedInItems(checkinStatusSet);
    } else {
      setCheckedInItems(new Set());
    }
  }, [checkinStatusSet]);

  // Batch check-in mutation
  const batchCheckInMutation = useMutation({
    mutationFn: async (planItemIds: string[]) => {
      return calendarService.batchCheckIn(userId, planItemIds, selectedDate);
    },
    onMutate: async (planItemIds: string[]) => {
      // Optimistically update UI immediately
      setCheckedInItems(prev => new Set([...prev, ...planItemIds]));
      return { planItemIds };
    },
    onSuccess: (data, planItemIds) => {
      toast({
        title: "Tasks Checked In",
        description: `${planItemIds.length} task(s) marked as completed.`,
      });
      
      // Clear selection after successful check-in
      setSelectedItems(new Set());
      
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: queryKeys.checkinStatus(userId) });
    },
    onError: (error, planItemIds, context) => {
      // Revert optimistic update on error
      if (context?.planItemIds) {
        setCheckedInItems(prev => {
          const newSet = new Set(prev);
          context.planItemIds.forEach(id => newSet.delete(id));
          return newSet;
        });
      }
      
      toast({
        title: "Check-in Failed",
        description: error.message || "Could not check in tasks. Please try again.",
        variant: "destructive",
      });
    }
  });

  // Handle batch check-in for selected items
  const handleBatchCheckIn = () => {
    const selectedPlanItemIds = Array.from(selectedItems);
    if (selectedPlanItemIds.length > 0) {
      batchCheckInMutation.mutate(selectedPlanItemIds);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Controls with Sync Button */}
      <Card>
        <CardContent>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              {/* Sync Check-ins Button */}
              <Button
                size="sm"
                variant="outline"
                onClick={() => refetchCheckinStatus()}
                disabled={checkinStatusLoading}
                className="text-xs"
              >
                <RefreshCw className={`w-4 h-4 mr-1 ${checkinStatusLoading ? 'animate-spin' : ''}`} />
                Sync Check-ins
              </Button>
              
              {/* Check-in Controls - Show when items are selected */}
              {selectedItems.size > 0 && (
                <Button
                  size="sm"
                  onClick={handleBatchCheckIn}
                  disabled={batchCheckInMutation.isPending || selectedItems.size === 0}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  <Check className="w-4 h-4 mr-1" />
                  Check In ({selectedItems.size})
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Task Items with Check-in Status */}
      {timeSlots.map((slot) => (
        <Card key={slot.hour}>
          <CardContent>
            {slot.items.map((item) => {
              const isSelected = selectedItems.has(item.id);
              const isCheckedIn = checkedInItems.has(item.id);
              
              return (
                <div key={item.id} className={`flex items-start gap-3 p-3 rounded-lg border transition-colors ${
                  isCheckedIn
                    ? 'bg-green-50 border-green-200' 
                    : isSelected
                    ? 'bg-yellow-50 border-yellow-200'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                }`}>
                  {/* Checkbox for batch selection */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleItemSelection(item.id)}
                    className={`p-1 h-auto hover:bg-white/50 ${
                      isSelected ? 'text-yellow-600' : 'text-gray-400 hover:text-gray-600'
                    }`}
                    disabled={isCheckedIn} // Disable selection for already checked-in items
                  >
                    {isSelected ? (
                      <CheckSquare className="w-4 h-4" />
                    ) : (
                      <Square className="w-4 h-4" />
                    )}
                  </Button>
                  
                  <div className="flex-1">
                    <h4 className={`font-medium mb-1 ${
                      isCheckedIn ? 'text-green-800 line-through' : 'text-gray-800'
                    }`}>{item.title}</h4>
                    
                    {/* Completed badge for checked-in items */}
                    {isCheckedIn && (
                      <Badge variant="default" className="text-xs bg-green-100 text-green-800">
                        <Check className="w-3 h-3 mr-1" />
                        ✅ Completed
                      </Badge>
                    )}
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      ))}
    </div>
  );
};
```

## Key Design Decisions

### 1. Simple MVP Approach

**Instead of complex date-based filtering**, we use:
- Single endpoint: `GET /checkins/status/{profile_id}` 
- Returns all completed `plan_item_ids` for the user
- Frontend does simple `Set.has(plan_item_id)` lookup - O(1) time complexity

**Benefits:**
- ✅ Dead simple logic
- ✅ Works across page refreshes
- ✅ No date confusion issues
- ✅ Fast performance
- ✅ Easy to debug

### 2. Optimistic UI Updates

Components immediately update the UI when user clicks check-in, then sync with server:
- **onMutate**: Update UI immediately for instant feedback
- **onSuccess**: Clear selections and invalidate cache
- **onError**: Revert optimistic changes and show error

### 3. React Query Integration

**Cache Strategy:**
- 30-second stale time for check-in status
- Manual refresh via "Sync Check-ins" button
- Automatic invalidation after mutations

**Query Keys:**
```typescript
queryKeys.checkinStatus(userId) // ['checkinStatus', 'user123']
```

### 4. Error Handling

**Graceful Degradation:**
- API failures return empty Set instead of crashing
- Error toasts inform users of issues
- Optimistic updates are reverted on failure

## Integration Flow

### 1. Adding Items to Calendar (Routine Plan Tab)

```typescript
// User clicks "Add to Calendar" button
const addToCalendar = async (planItemId: string) => {
  try {
    await calendarService.selectTasksForCalendar(userId, [planItemId]);
    toast({ title: "Added to calendar" });
    
    // Refresh calendar data
    queryClient.invalidateQueries({ queryKey: queryKeys.availablePlanItems(userId, date) });
  } catch (error) {
    toast({ title: "Failed to add to calendar", variant: "destructive" });
  }
};
```

### 2. Checking In Tasks (Calendar Tab)

```typescript
// User selects tasks and clicks "Check In"
const handleBatchCheckIn = () => {
  const selectedIds = Array.from(selectedItems);
  batchCheckInMutation.mutate(selectedIds);
};

// Mutation handles:
// 1. Optimistic UI update
// 2. API call to backend
// 3. Cache invalidation
// 4. Error handling with rollback
```

### 3. Persistence Across Sessions

```typescript
// On component mount or manual sync
const { data: checkinStatusSet } = useQuery({
  queryKey: queryKeys.checkinStatus(userId),
  queryFn: () => calendarService.getCheckinStatus(userId),
  staleTime: 30000, // 30 seconds
});

// Simple lookup in render
const isCheckedIn = checkinStatusSet?.has(item.id) || false;
```

## Testing Scenarios

### 1. Basic Flow Test
1. Add items from Routine Plan tab to calendar
2. Go to Calendar tab and verify items appear
3. Select items and check them in
4. Verify green checkmarks appear immediately
5. Refresh page - checkmarks should persist
6. Restart server - checkmarks should persist

### 2. Error Handling Test
1. Stop backend server
2. Try to check in items
3. Verify error toast appears
4. Verify UI reverts optimistic changes
5. Start server and click "Sync Check-ins"
6. Verify status is restored

### 3. Multi-Component Sync Test
1. Check in items in Calendar.tsx
2. Switch to CalendarSchedule.tsx
3. Verify same items are checked
4. Click "Sync Check-ins" in either component
5. Verify both components update consistently

## Performance Considerations

### 1. Caching Strategy
- **30-second stale time**: Balance between freshness and performance
- **Manual sync option**: User can force refresh when needed
- **Optimistic updates**: Instant UI feedback

### 2. Database Queries
- **Simple SELECT**: No complex JOINs for check-in status
- **UPSERT operations**: Prevent duplicate check-ins
- **Indexed columns**: profile_id and plan_item_id for fast lookups

### 3. Network Efficiency
- **Batch operations**: Multiple check-ins in single API call
- **Minimal payloads**: Only send necessary data
- **Error retry**: Automatic retry with exponential backoff

## Deployment Checklist

### Backend
- [ ] Database tables created with proper indexes
- [ ] API endpoints tested with Postman/curl
- [ ] Environment variables configured
- [ ] CORS settings allow frontend domain
- [ ] Error logging configured

### Frontend
- [ ] Environment variables set (VITE_DEV_API_URL)
- [ ] API configuration points to correct backend
- [ ] React Query devtools enabled for debugging
- [ ] Error boundaries implemented
- [ ] Toast notifications working

### Testing
- [ ] All basic flow scenarios pass
- [ ] Error handling tested
- [ ] Cross-component sync verified
- [ ] Performance under load tested
- [ ] Mobile responsiveness checked

## Common Issues and Solutions

### Issue: "ERR_CONNECTION_REFUSED"
**Cause**: Frontend trying to connect to wrong port
**Solution**: Check `.env` file has correct `VITE_DEV_API_URL`

### Issue: Check-ins don't persist after refresh
**Cause**: API not saving to database or wrong query
**Solution**: Check backend logs for database errors

### Issue: Optimistic updates not reverting on error
**Cause**: Missing error handling in mutations
**Solution**: Implement proper `onError` callbacks

### Issue: Components out of sync
**Cause**: Different query keys or cache invalidation issues
**Solution**: Use consistent query keys and invalidate properly

This implementation provides a robust, scalable foundation for calendar check-in functionality that can be easily replicated in other projects.