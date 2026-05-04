import client from './client'
import type { Approval } from '../types'

export const approvalApi = {
  list: async (status = 'pending'): Promise<Approval[]> => {
    const { data } = await client.get<Approval[]>('/approvals', { params: { status } })
    return data
  },

  approve: async (id: number, reviewer = 'admin', notes?: string): Promise<Approval> => {
    const { data } = await client.post<Approval>(`/approvals/${id}/approve`, { reviewer, notes })
    return data
  },

  reject: async (id: number, reviewer = 'admin', notes?: string): Promise<Approval> => {
    const { data } = await client.post<Approval>(`/approvals/${id}/reject`, { reviewer, notes })
    return data
  },
}
