import type { ReactNode } from 'react'
import styles from './styles.module.css'

interface ButtonProps {
  children: ReactNode,
  onClick: () => void
}

export function Button({children, onClick}: ButtonProps) {
  return (
    <button className={styles.button} onClick={onClick}>{children}</button>
  )
}