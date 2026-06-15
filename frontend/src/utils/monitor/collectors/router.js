import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'

import { enqueueMonitorEvent } from '../client'

export function MonitorRouteTracker() {
  const location = useLocation()
  const enteredAtRef = useRef(Date.now())
  const lastPathRef = useRef('')

  useEffect(() => {
    const route = `${location.pathname}${location.search || ''}`
    const previous = lastPathRef.current
    const now = Date.now()
    if (previous) {
      enqueueMonitorEvent({
        type: 'page_leave',
        name: 'page_leave',
        route: previous,
        payload: {
          duration_ms: now - enteredAtRef.current,
        },
      })
    }
    lastPathRef.current = route
    enteredAtRef.current = now
    enqueueMonitorEvent({
      type: 'page_view',
      name: 'page_view',
      route,
      payload: { referrer: document.referrer },
    })
  }, [location.pathname, location.search])

  useEffect(
    () => () => {
      if (lastPathRef.current) {
        enqueueMonitorEvent({
          type: 'page_leave',
          name: 'page_leave',
          route: lastPathRef.current,
          payload: {
            duration_ms: Date.now() - enteredAtRef.current,
          },
        })
      }
    },
    [],
  )

  return null
}
