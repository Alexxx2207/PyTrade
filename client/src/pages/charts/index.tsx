import { useState } from 'react';
import { Chart } from '../../components/chart';
import styles from './styles.module.css'
import Select, { type SingleValue, type StylesConfig } from 'react-select';
import { Button } from '../../components/button';
import { useAsyncAction } from '../../hooks/useAsyncAction';
import { indicatorService } from '../../services/indicators-service';

type InstrumentOptions = 'ES' | 'NQ'

type OptionType = {
  value: InstrumentOptions,
  label: string,
}

const options: OptionType[] = [
  { value: 'ES', label: 'ES' },
  { value: 'NQ', label: 'NQ' },
]

const selectStyle: StylesConfig<OptionType, false> = {
  option: (base, state) => ({
    ...base,
    color: state.isSelected ? "#fff" : state.isDisabled ? "#999" : "#111",
  }),
  menuPortal: (base: any) => ({ ...base, zIndex: 5 }),
  menu: (base: any) => ({ ...base, zIndex: 5 }),
}

export function ChartsPage() {
  const [instrument, setInstrument] = useState<OptionType | null>({value: 'ES', label: "ES"})
  const [minutesCount, setMinutesCount] = useState(60*24)
  const [workersCount, setWorkersCount] = useState(1)

  const {data: hurst, loading: loadingHurst, error: errorHurst, perform: getHurst} = useAsyncAction(() => indicatorService.getHurst(instrument!.value, minutesCount, workersCount))
  const {data: pe, loading: loadingPE, error: errorPE, perform: getPE} = useAsyncAction(() => indicatorService.getPermutationEntropy(instrument!.value, minutesCount, workersCount))

  if (!instrument) {
    return null;
  }

  return (
    <div className={styles.page}>
      <section>
      <h1>Instrument {instrument.value}</h1>
      <Select
        options={options} 
        value={instrument}
        onChange={(next: SingleValue<OptionType>) => setInstrument(next ?? null)} 
        styles={selectStyle}
        />
      </section>

      <section className={styles.indicators}>
        <div>
          <h3>Workers count:</h3>
          <input value={workersCount} onChange={(e) => {setWorkersCount(Number(e.target.value))}} />
        </div>
        <div className={styles.indicatorSection}>
          <Button onClick={() => getHurst()}>Get Hurst Exponent</Button>
          <span>
            {loadingHurst ? 
              "Loading..."
              :
              errorHurst ? "Error on fetching Hurst" : hurst
            }
          </span>
        </div>
        <div className={styles.indicatorSection}>
          <Button onClick={() => getPE()}>Get Permutation Entropy</Button>
          <span>
            {loadingPE ? 
              "Loading..."
              :
              errorPE ? "Error on fetching PE" : pe
            }
          </span>
        </div>
      </section>

      <Chart
        instrument={instrument.value}
        height={600}
        minutesCount={minutesCount}
        setMinutesCount={setMinutesCount}
      />
    </div>
  )
}

