import { api } from "./api"

export type Tick = {
  timestamp: number;
  price: number;
};

class InstrumentService {
    async getData(instrument: string, minutes: number) {
        const result = await api.get<Tick[]>(`/instruments/${instrument}?minutes=${minutes}`)
        
        return result
    }
}

export const instrumentService = new InstrumentService()
