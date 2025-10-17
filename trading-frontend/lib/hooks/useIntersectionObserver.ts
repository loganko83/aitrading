import { useEffect, useState, useRef } from 'react'

interface IntersectionObserverOptions {
  threshold?: number | number[]
  root?: Element | null
  rootMargin?: string
  freezeOnceVisible?: boolean
}

/**
 * Custom hook for Intersection Observer API
 * Useful for lazy loading, infinite scroll, and visibility tracking
 */
export function useIntersectionObserver(
  options: IntersectionObserverOptions = {}
): [React.RefObject<HTMLDivElement | null>, boolean] {
  const {
    threshold = 0,
    root = null,
    rootMargin = '0px',
    freezeOnceVisible = false,
  } = options

  const [isIntersecting, setIsIntersecting] = useState(false)
  const targetRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const target = targetRef.current

    if (!target) return

    // If already visible and frozen, skip observation
    if (freezeOnceVisible && isIntersecting) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting)
      },
      {
        threshold,
        root,
        rootMargin,
      }
    )

    observer.observe(target)

    return () => {
      if (target) {
        observer.unobserve(target)
      }
    }
  }, [threshold, root, rootMargin, freezeOnceVisible, isIntersecting])

  return [targetRef, isIntersecting]
}
