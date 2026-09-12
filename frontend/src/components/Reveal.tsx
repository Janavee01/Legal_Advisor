import { useEffect, useRef, useState, type ReactNode, type ElementType } from 'react'

export type RevealEffect =
  | 'up'
  | 'down'
  | 'left'
  | 'right'
  | 'zoom'
  | 'zoom-out'
  | 'flip'
  | 'blur'
  | 'rotate'

type RevealProps = {
  children: ReactNode
  className?: string
  delay?: number
  once?: boolean
  as?: ElementType
  id?: string
  effect?: RevealEffect
}

export function Reveal({
  children,
  className = '',
  delay = 0,
  once = false,
  as = 'div',
  id,
  effect = 'up',
}: RevealProps) {
  const ref = useRef<HTMLElement | null>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          if (once) observer.disconnect()
        } else if (!once) {
          setVisible(false)
        }
      },
      { threshold: 0.15, rootMargin: '0px 0px -10% 0px' }
    )

    observer.observe(el)
    return () => observer.disconnect()
  }, [once])

  const Tag = as

  return (
    <Tag
      ref={ref}
      id={id}
      className={`reveal reveal-${effect} ${visible ? 'reveal-visible' : ''} ${className}`}
      style={{ transitionDelay: visible ? `${delay}ms` : '0ms' }}
    >
      {children}
    </Tag>
  )
}