'use client'

import React, { Component, ReactNode } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AlertCircle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onReset?: () => void
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    this.props.onReset?.()
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <Card className="border-destructive">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-destructive" />
              <CardTitle>오류가 발생했습니다</CardTitle>
            </div>
            <CardDescription>
              {this.state.error?.message || '알 수 없는 오류가 발생했습니다'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={this.handleReset} variant="outline" className="gap-2">
              <RefreshCw className="h-4 w-4" />
              다시 시도
            </Button>
          </CardContent>
        </Card>
      )
    }

    return this.props.children
  }
}

/**
 * Simple error fallback component
 */
export function ErrorFallback({
  error,
  resetError
}: {
  error: Error
  resetError: () => void
}) {
  return (
    <div className="flex items-center justify-center min-h-[200px] p-4">
      <Card className="border-destructive max-w-md w-full">
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <CardTitle>오류가 발생했습니다</CardTitle>
          </div>
          <CardDescription>
            {error.message || '알 수 없는 오류가 발생했습니다'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={resetError} variant="outline" className="gap-2">
            <RefreshCw className="h-4 w-4" />
            다시 시도
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
