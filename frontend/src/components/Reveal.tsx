import React, {
  useEffect,
  useRef,
  useState,
  type ReactNode,
  type CSSProperties,
} from 'react'

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
  as?: 'div' | 'a' | 'section' | 'li'
  id?: string
  href?: string
  effect?: RevealEffect
  style?: CSSProperties
}

export function Reveal({
  children,
  className = '',
  delay = 0,
  once = false,
  as = 'div',
  id,
  href,
  effect = 'up',
  style,
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

          if (once) {
            observer.disconnect()
          }
        } else if (!once) {
          setVisible(false)
        }
      },
      {
        threshold: 0.15,
        rootMargin: '0px 0px -10% 0px',
      }
    )

    observer.observe(el)

    return () => observer.disconnect()
  }, [once])

  const classes = `reveal reveal-${effect} ${
    visible ? 'reveal-visible' : ''
  } ${className}`

  const combinedStyle: CSSProperties = {
    ...style,
    transitionDelay: visible ? `${delay}ms` : '0ms',
  }

  if (as === 'a') {
    return (
      <a
        ref={ref as React.RefObject<HTMLAnchorElement>}
        id={id}
        href={href}
        className={classes}
        style={combinedStyle}
      >
        {children}
      </a>
    )
  }

  if (as === 'section') {
    return (
      <section
        ref={ref as React.RefObject<HTMLElement>}
        id={id}
        className={classes}
        style={combinedStyle}
      >
        {children}
      </section>
    )
  }

  if (as === 'li') {
    return (
      <li
        ref={ref as React.RefObject<HTMLLIElement>}
        id={id}
        className={classes}
        style={combinedStyle}
      >
        {children}
      </li>
    )
  }

  return (
    <div
      ref={ref as React.RefObject<HTMLDivElement>}
      id={id}
      className={classes}
      style={combinedStyle}
    >
      {children}
    </div>
  )
}