import { api } from "./api"

export type Tick = {
  timestamp: number;
  price: number;
};

class InstrumentService {
    async getData(instrument: string) {
        const result = await api.get<{prices: Tick[]}>(`/instruments/${instrument}`)

        return result.prices
    }
}

export const instrumentService = new InstrumentService()
