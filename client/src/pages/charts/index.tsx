import { useState } from 'react';
import { Chart } from '../../components/chart';
import styles from './styles.module.css'

export function ChartsPage() {
  const [instrument, _setInstrument] = useState('ES')
  
  return (
    <div className={styles.page}>
      <h1>Instrument {instrument}</h1>
      <Chart instrument={instrument} height={600}/>
    </div>
  )
}

