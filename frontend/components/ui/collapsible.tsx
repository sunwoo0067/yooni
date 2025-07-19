import * as React from "react"

interface CollapsibleProps extends React.HTMLAttributes<HTMLDivElement> {
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

const Collapsible = React.forwardRef<HTMLDivElement, CollapsibleProps>(
  ({ className = '', open = false, onOpenChange, children, ...props }, ref) => {
    const [isOpen, setIsOpen] = React.useState(open)

    React.useEffect(() => {
      setIsOpen(open)
    }, [open])

    return (
      <div ref={ref} className={className} {...props}>
        {React.Children.map(children, child => {
          if (React.isValidElement(child)) {
            return React.cloneElement(child, {
              isOpen,
              setIsOpen: (value: boolean) => {
                setIsOpen(value)
                onOpenChange?.(value)
              }
            } as any)
          }
          return child
        })}
      </div>
    )
  }
)
Collapsible.displayName = "Collapsible"

const CollapsibleTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { isOpen?: boolean; setIsOpen?: (open: boolean) => void }
>(({ className = '', isOpen, setIsOpen, onClick, ...props }, ref) => (
  <button
    ref={ref}
    className={className}
    onClick={(e) => {
      setIsOpen?.(!isOpen)
      onClick?.(e)
    }}
    {...props}
  />
))
CollapsibleTrigger.displayName = "CollapsibleTrigger"

const CollapsibleContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { isOpen?: boolean }
>(({ className = '', isOpen, ...props }, ref) => (
  <div
    ref={ref}
    className={className}
    style={{ display: isOpen ? 'block' : 'none' }}
    {...props}
  />
))
CollapsibleContent.displayName = "CollapsibleContent"

export { Collapsible, CollapsibleTrigger, CollapsibleContent }