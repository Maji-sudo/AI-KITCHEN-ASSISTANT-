import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationService } from '@/services/notification.service'
import type { Notification } from '@/types'

export const NOTIFICATIONS_QUERY_KEY = ['notifications']
export const UNREAD_COUNT_QUERY_KEY = ['notifications', 'unread-count']

export function useNotifications(filter?: string, unreadOnly = false) {
  const queryClient = useQueryClient()

  const {
    data: notifications = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<Notification[]>({
    queryKey: [...NOTIFICATIONS_QUERY_KEY, filter, unreadOnly],
    queryFn: () => notificationService.getAll(0, 50, filter, unreadOnly),
    staleTime: 10 * 1000,
    refetchInterval: 15 * 1000, // Poll every 15s for live telemetry & safety notifications
  })

  const { data: unreadCount = 0 } = useQuery<number>({
    queryKey: UNREAD_COUNT_QUERY_KEY,
    queryFn: () => notificationService.getUnreadCount(),
    staleTime: 10 * 1000,
    refetchInterval: 15 * 1000,
  })

  const markReadMutation = useMutation({
    mutationFn: (id: number) => notificationService.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: UNREAD_COUNT_QUERY_KEY })
    },
  })

  const markAllReadMutation = useMutation({
    mutationFn: () => notificationService.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: UNREAD_COUNT_QUERY_KEY })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => notificationService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: UNREAD_COUNT_QUERY_KEY })
    },
  })

  const clearMutation = useMutation({
    mutationFn: (all?: boolean) => notificationService.clear(all ?? false),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: UNREAD_COUNT_QUERY_KEY })
    },
  })

  return {
    notifications,
    unreadCount,
    isLoading,
    isError,
    error,
    refetch,
    markAsRead: markReadMutation.mutate,
    markAllAsRead: markAllReadMutation.mutate,
    deleteNotification: deleteMutation.mutate,
    clearNotifications: clearMutation.mutate,
    isMarkingRead: markReadMutation.isPending,
    isMarkingAllRead: markAllReadMutation.isPending,
  }
}
