import React, { useState, useEffect } from 'react'
import { Modal, Button, StatusBadge } from '../components'
import { api, floatToTime, hourToDateAndTimeString } from '../api/client'
import { useApp } from '../context/AppContext'
import type { ScheduleTask } from '../types'
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Wrench,
  Save,
  X,
  Info,
  Layers,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react'

interface OperationEditorModalProps {
  task: ScheduleTask | null
  onClose: () => void
}

export function OperationEditorModal({ task, onClose }: OperationEditorModalProps) {
  const { proposedScheduleId, updateDraftOperation, machines } = useApp()

  const [selectedMachine, setSelectedMachine] = useState<string>('')
  const [startHour, setStartHour] = useState<number>(0)
  const [duration, setDuration] = useState<number>(2.0)
  const [eligibleMachines, setEligibleMachines] = useState<Array<{
    machine_id: string
    name: string
    machine_type: string
    available: boolean
    utilization: number
    current_task: string | null
    is_compatible: boolean
    incompatibility_reason: string | null
  }>>([])
  const [loadingMachines, setLoadingMachines] = useState(false)
  const [saving, setSaving] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!task) return

    setSelectedMachine(task.machineId)
    const initStart = task.startHour !== undefined ? task.startHour : 0
    setStartHour(initStart)
    const initDur = task.duration !== undefined ? task.duration : 2.0
    setDuration(initDur)
    setErrorMessage(null)

    // Fetch eligible machines from backend
    if (proposedScheduleId) {
      setLoadingMachines(true)
      api
        .getEligibleMachinesForOp(proposedScheduleId, task.id)
        .then((data) => {
          setEligibleMachines(data)
        })
        .catch((err) => {
          console.warn('Could not load eligible machines:', err)
          // Fallback to all local machines
          setEligibleMachines(
            machines.map((m) => ({
              machine_id: m.id,
              name: m.name,
              machine_type: m.type,
              available: m.status !== 'Breakdown',
              utilization: m.utilization,
              current_task: m.task,
              is_compatible: true,
              incompatibility_reason: null,
            }))
          )
        })
        .finally(() => setLoadingMachines(false))
    }
  }, [task, proposedScheduleId, machines])

  if (!task) return null

  const endHour = Number((startHour + duration).toFixed(2))
  const startTimeObj = hourToDateAndTimeString(startHour)
  const endTimeObj = hourToDateAndTimeString(endHour)

  const handleSave = async () => {
    if (!selectedMachine) {
      setErrorMessage('Please select a valid machine.')
      return
    }
    if (duration <= 0) {
      setErrorMessage('Duration must be greater than zero.')
      return
    }

    setSaving(true)
    setErrorMessage(null)
    const res = await updateDraftOperation(task.id, selectedMachine, startHour, endHour)
    setSaving(false)

    if (res.success) {
      onClose()
    } else {
      setErrorMessage(res.error || 'Failed to update operation.')
    }
  }

  const selectedMachineInfo = eligibleMachines.find((m) => m.machine_id === selectedMachine)

  return (
    <Modal
      open={!!task}
      title={`Modify Operation: ${task.id}`}
      subtitle={`${task.orderId} · ${task.product} (${task.operationName || 'Production'})`}
      onClose={onClose}
      wide={false}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Operation Summary Header */}
        <div
          style={{
            background: '#f8faf9',
            border: '1px solid #e1e7e4',
            borderRadius: 8,
            padding: '12px 16px',
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 12,
            fontSize: 12,
          }}
        >
          <div>
            <span style={{ color: '#687771', display: 'block', fontSize: 10, textTransform: 'uppercase', fontWeight: 600 }}>
              Order / Product
            </span>
            <strong style={{ color: '#1a2e2b' }}>{task.orderId} · {task.product}</strong>
          </div>
          <div>
            <span style={{ color: '#687771', display: 'block', fontSize: 10, textTransform: 'uppercase', fontWeight: 600 }}>
              Operation Step
            </span>
            <strong style={{ color: '#1a2e2b' }}>{task.operationName || task.id}</strong>
          </div>
          <div>
            <span style={{ color: '#687771', display: 'block', fontSize: 10, textTransform: 'uppercase', fontWeight: 600 }}>
              Original Machine
            </span>
            <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#365c55' }}>{task.machineId}</span>
          </div>
          <div>
            <span style={{ color: '#687771', display: 'block', fontSize: 10, textTransform: 'uppercase', fontWeight: 600 }}>
              Current Status
            </span>
            <StatusBadge value={task.status as any} />
          </div>
        </div>

        {/* Backend Conflict Error Display */}
        {errorMessage && (
          <div
            style={{
              padding: '12px 14px',
              background: '#fff2f0',
              border: '1px solid #f9d2ce',
              borderRadius: 8,
              display: 'flex',
              gap: 10,
              alignItems: 'flex-start',
            }}
          >
            <ShieldAlert size={18} style={{ color: '#dc2626', flexShrink: 0, marginTop: 2 }} />
            <div>
              <strong style={{ color: '#991b1b', fontSize: 12, display: 'block', marginBottom: 2 }}>
                Validation Conflict
              </strong>
              <span style={{ color: '#7f1d1d', fontSize: 11, lineHeight: 1.4 }}>{errorMessage}</span>
            </div>
          </div>
        )}

        {/* Assigned Machine Selector */}
        <div>
          <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: '#2b3b36', marginBottom: 6 }}>
            Assigned Machine (Eligible Alternatives)
          </label>
          <select
            value={selectedMachine}
            onChange={(e) => {
              setSelectedMachine(e.target.value)
              setErrorMessage(null)
            }}
            disabled={saving || loadingMachines}
            style={{
              width: '100%',
              padding: '8px 12px',
              borderRadius: 6,
              border: '1px solid #c9d5d0',
              background: '#ffffff',
              fontSize: 13,
              color: '#1a2e2b',
              outline: 'none',
            }}
          >
            {eligibleMachines.map((m) => (
              <option
                key={m.machine_id}
                value={m.machine_id}
                disabled={!m.is_compatible}
                style={{ color: m.is_compatible ? '#1a2e2b' : '#94a3b8' }}
              >
                {m.machine_id} · {m.name} {!m.is_compatible ? '(Incompatible)' : !m.available ? '(Offline / Breakdown)' : `(Util: ${m.utilization}%)`}
              </option>
            ))}
          </select>

          {selectedMachineInfo && !selectedMachineInfo.is_compatible && (
            <div style={{ marginTop: 4, fontSize: 11, color: '#dc2626', display: 'flex', alignItems: 'center', gap: 4 }}>
              <AlertTriangle size={12} />
              {selectedMachineInfo.incompatibility_reason || 'This machine does not support this operation.'}
            </div>
          )}
          {selectedMachineInfo && !selectedMachineInfo.available && (
            <div style={{ marginTop: 4, fontSize: 11, color: '#d97706', display: 'flex', alignItems: 'center', gap: 4 }}>
              <AlertTriangle size={12} />
              Machine is currently offline or under breakdown downtime.
            </div>
          )}
        </div>

        {/* Schedule Timing Inputs */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {/* Start Time */}
          <div>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: '#2b3b36', marginBottom: 6 }}>
              Start Hour (from shift base 06:00)
            </label>
            <input
              type="number"
              step="0.5"
              min="0"
              value={startHour}
              onChange={(e) => {
                setStartHour(Math.max(0, parseFloat(e.target.value) || 0))
                setErrorMessage(null)
              }}
              disabled={saving}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: 6,
                border: '1px solid #c9d5d0',
                background: '#ffffff',
                fontSize: 13,
                color: '#1a2e2b',
              }}
            />
            <div style={{ marginTop: 4, fontSize: 11, color: '#4b635c', display: 'flex', alignItems: 'center', gap: 4 }}>
              <Clock size={12} />
              <span>Clock: <strong>{startTimeObj.time}</strong> ({startTimeObj.date})</span>
            </div>
          </div>

          {/* Duration */}
          <div>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: '#2b3b36', marginBottom: 6 }}>
              Duration (Hours)
            </label>
            <input
              type="number"
              step="0.5"
              min="0.5"
              value={duration}
              onChange={(e) => {
                setDuration(Math.max(0.1, parseFloat(e.target.value) || 0.1))
                setErrorMessage(null)
              }}
              disabled={saving}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: 6,
                border: '1px solid #c9d5d0',
                background: '#ffffff',
                fontSize: 13,
                color: '#1a2e2b',
              }}
            />
            <div style={{ marginTop: 4, fontSize: 11, color: '#4b635c', display: 'flex', alignItems: 'center', gap: 4 }}>
              <Clock size={12} />
              <span>Ends: <strong>{endTimeObj.time}</strong> ({endTimeObj.date})</span>
            </div>
          </div>
        </div>

        {/* Shift Window Visual Indicator */}
        <div
          style={{
            padding: '10px 14px',
            background: '#eef5f2',
            border: '1px solid #d4e4dc',
            borderRadius: 6,
            fontSize: 11,
            color: '#284640',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span>
            Window: <strong>{startTimeObj.time}</strong> <ArrowRight size={12} style={{ display: 'inline', margin: '0 4px' }} /> <strong>{endTimeObj.time}</strong> ({duration.toFixed(1)} hrs)
          </span>
          <span style={{ fontSize: 10, color: '#55726a' }}>
            Base shift: 06:00 – 22:00
          </span>
        </div>

        {/* Modal Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
          <Button variant="outline" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSave}
            disabled={saving || (selectedMachineInfo && !selectedMachineInfo.is_compatible)}
            icon={saving ? <Clock className="spin" size={14} /> : <Save size={14} />}
          >
            {saving ? 'Validating & Saving…' : 'Save Changes'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

