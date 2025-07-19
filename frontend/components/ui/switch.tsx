import * as React from "react"

export interface SwitchProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'onChange'> {
  checked?: boolean
  onCheckedChange?: (checked: boolean) => void
}

const Switch = React.forwardRef<HTMLButtonElement, SwitchProps>(
  ({ className = '', checked = false, onCheckedChange, ...props }, ref) => {
    const [isChecked, setIsChecked] = React.useState(checked)

    React.useEffect(() => {
      setIsChecked(checked)
    }, [checked])

    const handleClick = () => {
      const newChecked = !isChecked
      setIsChecked(newChecked)
      onCheckedChange?.(newChecked)
    }

    return (
      <button
        type="button"
        role="switch"
        aria-checked={isChecked}
        className={`peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50 ${
          isChecked ? 'bg-primary' : 'bg-input'
        } ${className}`}
        ref={ref}
        onClick={handleClick}
        {...props}
      >
        <span
          className={`pointer-events-none block h-4 w-4 rounded-full bg-background shadow-lg ring-0 transition-transform ${
            isChecked ? 'translate-x-4' : 'translate-x-0'
          }`}
        />
      </button>
    )
  }
)
Switch.displayName = "Switch"

export { Switch }