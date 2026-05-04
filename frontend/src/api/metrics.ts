import client from './client'
import type { MetricsBreakdown, MetricsSummary, VolumeDataPoint } from '../types'

export const metricsApi = {
  summary: async (): Promise<MetricsSummary> => {
    const { data } = await client.get<MetricsSummary>('/metrics/summary')
    return data
  },

  volume: async (days = 7): Promise<VolumeDataPoint[]> => {
    const { data } = await client.get<VolumeDataPoint[]>('/metrics/volume', { params: { days } })
    return data
  },

  breakdown: async (): Promise<MetricsBreakdown> => {
    const { data } = await client.get<MetricsBreakdown>('/metrics/breakdown')
    return data
  },
}
