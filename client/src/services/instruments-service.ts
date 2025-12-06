import { api } from "./api"

export type Tick = {
  timestamp: number;
  price: number;
};

class InstrumentService {
    async getData(instrument: string, ticks: number) {
        const result = await api.get<{prices: Tick[]}>(`/instruments/${instrument}?ticks=${ticks}`)

        return result.prices
    }
}

export const instrumentService = new InstrumentService()
