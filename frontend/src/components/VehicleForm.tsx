import { useState } from 'react'
import type { FormEvent } from 'react'
import { errorMessage } from '../api'
import type { VehicleInput } from '../types'

type Props = {
  initial: VehicleInput | null // null = nové auto, inak upravujeme existujúce
  onSave: (data: VehicleInput) => Promise<void>
  onCancel: () => void
}

function VehicleForm({ initial, onSave, onCancel }: Props) {
  // Počiatočná hodnota sa použije len pri prvom zobrazení formulára.
  const [brand, setBrand] = useState(initial?.brand ?? '')
  const [model, setModel] = useState(initial?.model ?? '')
  const [licensePlate, setLicensePlate] = useState(initial?.license_plate ?? '')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await onSave({ brand, model, license_plate: licensePlate })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2>{initial === null ? 'Nové auto' : 'Upraviť auto'}</h2>

      {/* required, maxLength a pattern skontroluje prehliadač ešte pred odoslaním. */}
      <label>
        Značka
        <input value={brand} onChange={(e) => setBrand(e.target.value)} required maxLength={50} />
      </label>

      <label>
        Model
        <input value={model} onChange={(e) => setModel(e.target.value)} required maxLength={50} />
      </label>

      <label>
        ŠPZ
        <input
          value={licensePlate}
          onChange={(e) => setLicensePlate(e.target.value)}
          required
          pattern="[A-Za-z0-9 \-]+"
          title="Len písmená, číslice, medzery a pomlčky"
        />
      </label>

      {error && <p className="error">{error}</p>}

      <div className="actions">
        <button type="submit" disabled={saving}>
          {saving ? 'Ukladám…' : 'Uložiť'}
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Zrušiť
        </button>
      </div>
    </form>
  )
}

export default VehicleForm
