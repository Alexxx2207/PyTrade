import { Chart } from '../../components/chart';
import styles from './styles.module.css'

export function ChartsPage() {
  return (
    <div className={styles.page}>
      <Chart instrument='ES' height={600}/>
    </div>
  )
}

