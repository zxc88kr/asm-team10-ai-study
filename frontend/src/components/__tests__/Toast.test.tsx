import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import Toast from '../Toast'
import useAppStore from '../../store/useAppStore'

beforeEach(() => {
  act(() => useAppStore.getState().reset())
})

describe('Toast', () => {
  it('toastMessage가 없으면 아무것도 렌더링하지 않음', () => {
    const { container } = render(<Toast />)
    expect(container).toBeEmptyDOMElement()
  })

  it('toastMessage가 있으면 텍스트를 렌더링', () => {
    act(() => useAppStore.setState({ toastMessage: '저장되었습니다' }))
    render(<Toast />)
    expect(screen.getByText('저장되었습니다')).toBeInTheDocument()
  })

  it('show 클래스가 적용됨', () => {
    act(() => useAppStore.setState({ toastMessage: '알림' }))
    render(<Toast />)
    const el = screen.getByText('알림')
    expect(el.className).toContain('toast')
    expect(el.className).toContain('show')
  })
})
