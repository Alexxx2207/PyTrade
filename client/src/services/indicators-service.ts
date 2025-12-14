import { api } from "./api"

class IndicatorService {
  async getHurst(instrument: string, minutes: number, workers: number) {
    return await api.get<number>(`/instruments/${instrument}/hurst?minutes=${minutes}&workers=${workers}`)
  }

  async getPermutationEntropy(instrument: string, minutes: number, workers: number) {
    return await api.get<number>(`/instruments/${instrument}/permutation-entropy?minutes=${minutes}&workers=${workers}`)
  }
}

export const indicatorService = new IndicatorService()
