import client from './client'
import type { Process, ProcessDetail, ProcessListResponse } from '../types'

export interface ProcessFilters {
  page?: number
  per_page?: number
  status?: string
  process_type?: string
  priority?: string
  search?: string
}

export const processApi = {
  list: async (filters: ProcessFilters = {}): Promise<ProcessListResponse> => {
    const params = Object.fromEntries(
      Object.entries(filters).filter(([, v]) => v !== undefined && v !== '')
    )
    const { data } = await client.get<ProcessListResponse>('/processes', { params })
    return data
  },

  get: async (id: number): Promise<ProcessDetail> => {
    const { data } = await client.get<ProcessDetail>(`/processes/${id}`)
    return data
  },

  submit: async (source: string, rawInput: string) => {
    const { data } = await client.post('/ingestion/submit', {
      source,
      raw_input: rawInput,
    })
    return data
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/processes/${id}`)
  },
}
