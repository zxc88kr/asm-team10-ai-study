import { useEffect, useRef, useState } from 'react'
import useAppStore from '../store/useAppStore'

export default function Toast() {
  const toastMessage = useAppStore(s => s.toastMessage)
  const [text, setText] = useState('')
  const [show, setShow] = useState(false)
  const fadeTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (toastMessage) {
      if (fadeTimer.current !== null) clearTimeout(fadeTimer.current)
      setText(toastMessage)
      setShow(true)
    } else {
      setShow(false)
      fadeTimer.current = setTimeout(() => setText(''), 300)
    }
    return () => {
      if (fadeTimer.current !== null) clearTimeout(fadeTimer.current)
    }
  }, [toastMessage])

  if (!text) return null

  return <div className={`toast${show ? ' show' : ''}`}>{text}</div>
}
