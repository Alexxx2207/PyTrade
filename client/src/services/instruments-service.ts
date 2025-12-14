import { api } from "./api"

export type Tick = {
  timestamp: number;
  price: number;
};

class InstrumentService {
    async getData(instrument: string, minutes: number) {
        return await api.get<Tick[]>(`/instruments/${instrument}?minutes=${minutes}`)
    }
}

export const instrumentService = new InstrumentService()
