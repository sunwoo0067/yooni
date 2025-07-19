import { toast } from 'sonner'

export function useToast() {
  return {
    toast: (options: { title?: string; description?: string; variant?: 'default' | 'destructive' }) => {
      if (options.variant === 'destructive') {
        toast.error(options.title || options.description)
      } else {
        toast.success(options.title || options.description)
      }
    }
  }
}

export { toast }