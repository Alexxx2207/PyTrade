import { api } from "./api"

class InstrumentService {
    async getData(instrument: string) {
        return api.get<{ instrument: string }>(`/instruments/${instrument}`)
    }
}

export const instrumentService = new InstrumentService()
