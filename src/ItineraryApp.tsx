import { useState, useEffect, useRef, useCallback } from 'react'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// ─── Types ────────────────────────────────────────────────────────────────────

type ActivityType = 'beach' | 'boat' | 'culture' | 'walk' | 'food'

interface Destination {
  name: string
  coords: [number, number]
  distance: string
  time: string
  note: string
}

interface Day {
  id: string
  shortDay: string
  dayNum: string
  month: string
  emoji: string
  type: ActivityType
  title: string
  subtitle: string
  destinations: Destination[]
  tips: string[]
  mapCenter: [number, number]
  mapZoom: number
}

interface Stay {
  id: string
  name: string
  coords: [number, number]
  nights: number
  period: string
  region: string
  accent: string
  days: Day[]
}

// ─── Data ─────────────────────────────────────────────────────────────────────

const STAYS: Stay[] = [
  {
    id: 'cannigione',
    name: 'Cannigione',
    coords: [41.083, 9.526],
    nights: 4,
    period: 'June 26 – 29',
    region: 'Costa Smeralda · North Sardinia',
    accent: '#1d6b9e',
    days: [
      {
        id: 'jun26',
        shortDay: 'FRI',
        dayNum: '26',
        month: 'JUN',
        emoji: '🏖️',
        type: 'beach',
        title: 'Porto Cervo & Beach Day',
        subtitle: 'Costa Smeralda — glamour + crystal water',
        destinations: [
          {
            name: 'Capriccioli Beach',
            coords: [41.090, 9.492],
            distance: '12 km',
            time: '18 min',
            note: 'Pristine granite-framed cove — arrive early to get a spot'
          },
          {
            name: 'Spiaggia del Principe',
            coords: [41.083, 9.475],
            distance: '14 km',
            time: '20 min',
            note: "Aga Khan's favourite — one of Sardinia's finest beaches"
          },
          {
            name: 'Porto Cervo',
            coords: [41.133, 9.517],
            distance: '15 km',
            time: '20 min',
            note: 'Chic marina for a stroll, nice lunch, and evening aperitivo'
          },
        ],
        tips: [
          'Arrive at the beach by 9am for a good spot',
          'Pick ONE beach — Capriccioli has easier parking',
          'Lunch at a beach lido (€15–25 pp)',
          'End with aperitivo at Porto Cervo old port',
        ],
        mapCenter: [41.108, 9.500],
        mapZoom: 12,
      },
      {
        id: 'jun27',
        shortDay: 'SAT',
        dayNum: '27',
        month: 'JUN',
        emoji: '⛵',
        type: 'boat',
        title: 'La Maddalena Archipelago',
        subtitle: 'Full day boat excursion — National Park',
        destinations: [
          {
            name: 'Palau — departure point',
            coords: [41.183, 9.383],
            distance: '20 km',
            time: '25 min',
            note: 'Join a group excursion or hire a private boat here'
          },
          {
            name: 'La Maddalena Archipelago',
            coords: [41.217, 9.400],
            distance: '—',
            time: 'Full day on water',
            note: 'Pink granite, transparent sea, hidden beaches — National Park'
          },
        ],
        tips: [
          'Book the excursion 1–2 days ahead (fills up fast)',
          'Pack snorkelling gear, sunscreen, plenty of water',
          'Best beaches: Budelli (pink sand), Spargi, Cala Coticcio',
          'Full day — no other plans needed',
        ],
        mapCenter: [41.200, 9.390],
        mapZoom: 11,
      },
      {
        id: 'jun28',
        shortDay: 'SUN',
        dayNum: '28',
        month: 'JUN',
        emoji: '🌊',
        type: 'walk',
        title: 'Capo Testa & Santa Teresa',
        subtitle: 'Coastal walk through granite boulders + seafood dinner',
        destinations: [
          {
            name: 'Capo Testa',
            coords: [41.233, 9.133],
            distance: '57 km',
            time: '55 min',
            note: 'Surreal granite rock formations + hidden swimming coves'
          },
          {
            name: 'Santa Teresa di Gallura',
            coords: [41.239, 9.188],
            distance: '53 km',
            time: '50 min',
            note: '3 km from Capo Testa — great town for a seafood dinner'
          },
        ],
        tips: [
          'Coastal walk among the boulders (flat, 1–2h, bring water)',
          'Swim in the coves between the rock formations',
          'Drive 3 km to Santa Teresa for dinner — try the tuna',
          'Sunset from the Spanish tower above town is spectacular',
        ],
        mapCenter: [41.237, 9.160],
        mapZoom: 12,
      },
      {
        id: 'jun29',
        shortDay: 'MON',
        dayNum: '29',
        month: 'JUN',
        emoji: '🏰',
        type: 'culture',
        title: 'Castelsardo → Alghero',
        subtitle: 'Check-out day — culture stop en route to Stay 2',
        destinations: [
          {
            name: 'Castelsardo',
            coords: [40.917, 8.717],
            distance: '100 km',
            time: '1h 20 min',
            note: 'Medieval hilltop town on a sea promontory — stunning views'
          },
          {
            name: 'Alghero ★ check in',
            coords: [40.558, 8.317],
            distance: '170 km total',
            time: '+55 min from Castelsardo',
            note: 'Catalan-influenced city with beautiful walled old town'
          },
        ],
        tips: [
          'Check out early from Cannigione (~9am)',
          'Explore the medieval old town + cathedral',
          'Lunch with a sea view in Castelsardo',
          'Leave by 14:00 → arrive Alghero ~15:00',
          'Evening stroll along the seafront ramparts of Alghero',
        ],
        mapCenter: [40.740, 8.520],
        mapZoom: 9,
      },
    ],
  },
  {
    id: 'alghero',
    name: 'Alghero',
    coords: [40.558, 8.317],
    nights: 4,
    period: 'June 29 – July 3',
    region: 'Riviera del Corallo · West Sardinia',
    accent: '#c0522b',
    days: [
      {
        id: 'jun30',
        shortDay: 'TUE',
        dayNum: '30',
        month: 'JUN',
        emoji: '🏖️',
        type: 'beach',
        title: 'Beach Day — Full Relax',
        subtitle: 'Pick a beach and stay all day — zero sightseeing',
        destinations: [
          {
            name: 'Le Bombarde',
            coords: [40.600, 8.250],
            distance: '8 km',
            time: '12 min',
            note: 'Long sandy beach, good facilities, calm clear water'
          },
          {
            name: 'Mugoni Beach',
            coords: [40.617, 8.200],
            distance: '12 km',
            time: '18 min',
            note: 'Inside a nature reserve — quieter and more scenic'
          },
        ],
        tips: [
          'Pick ONE and commit — no rushing between beaches',
          'Le Bombarde: easier parking, more facilities',
          'Mugoni: prettier setting, slightly harder to reach',
          'Lunch and dinner right by the beach',
        ],
        mapCenter: [40.608, 8.230],
        mapZoom: 12,
      },
      {
        id: 'jul1',
        shortDay: 'WED',
        dayNum: '1',
        month: 'JUL',
        emoji: '🕳️',
        type: 'culture',
        title: "Neptune's Grotto",
        subtitle: 'Spectacular sea cave — boat from Alghero is the best way',
        destinations: [
          {
            name: "Neptune's Grotto (Capo Caccia)",
            coords: [40.567, 8.160],
            distance: '25 km',
            time: '30 min by car  |  boat from port',
            note: 'Massive stalactite cave at sea level — 654 steps down by car'
          },
        ],
        tips: [
          '⭐ Best option: boat from Alghero port (~2h scenic round trip)',
          'By car: park at Capo Caccia → 654 steps down the cliff (Escala del Cabriol)',
          'Book grotto entry online to skip the queue',
          'Bring a light jacket — cave stays at 14°C',
          'Swim at the foot of the cliffs after the visit',
        ],
        mapCenter: [40.567, 8.160],
        mapZoom: 11,
      },
      {
        id: 'jul2',
        shortDay: 'THU',
        dayNum: '2',
        month: 'JUL',
        emoji: '🎨',
        type: 'walk',
        title: 'Bosa',
        subtitle: 'Pastel village on the Temo river — slow and beautiful',
        destinations: [
          {
            name: 'Bosa',
            coords: [40.298, 8.498],
            distance: '50 km',
            time: '50 min',
            note: 'Colourful houses, Temo river, Malaspina castle'
          },
        ],
        tips: [
          'Slow morning in Alghero — depart around 10–11am',
          'Walk the riverside and colourful old town',
          'Lunch at a riverfront terrace restaurant',
          'Walk up to Malaspina castle for panoramic views',
          'Try Malvasia di Bosa wine at a local cantina on the way back',
        ],
        mapCenter: [40.298, 8.498],
        mapZoom: 12,
      },
      {
        id: 'jul3',
        shortDay: 'FRI',
        dayNum: '3',
        month: 'JUL',
        emoji: '✈️',
        type: 'food',
        title: 'Last Lunch → Olbia Airport',
        subtitle: 'Flight 20:40 — leave Alghero by 17:00',
        destinations: [
          {
            name: 'Alghero old town — last lunch',
            coords: [40.558, 8.317],
            distance: '—',
            time: 'Walk from hotel',
            note: 'Last seafront lunch on the ramparts — enjoy every bite'
          },
          {
            name: 'Olbia Airport (OLB)',
            coords: [40.898, 9.518],
            distance: '135 km',
            time: '1h 45 min',
            note: 'Arrive by 18:40 for a 20:40 departure (2h before)'
          },
        ],
        tips: [
          'Relaxed morning — last swim or coffee on the seafront',
          '⚠️ Leave Alghero by 17:00 at the latest',
          '135 km drive (~1h 45 min) to Olbia',
          'Return rental car before terminal check-in',
          'Target OLB arrival: 18:40 (2h before departure)',
        ],
        mapCenter: [40.728, 8.917],
        mapZoom: 9,
      },
    ],
  },
]

// ─── Airport ──────────────────────────────────────────────────────────────────

const AIRPORT = {
  name: 'Olbia Airport (OLB)',
  coords: [40.898, 9.518] as [number, number],
  arrivalTo: 'Cannigione',
  arrivalCoords: [41.083, 9.526] as [number, number],
  arrivalDistance: '35 km',
  arrivalTime: '~35 min',
  arrivalNote: 'Via SS125 — straight drive, no tolls',
}

// ─── Activity badge config ─────────────────────────────────────────────────────

const ACTIVITY = {
  beach:   { label: 'Beach',   bg: '#fef3c7', text: '#92400e', dot: '#f59e0b' },
  boat:    { label: 'Boat',    bg: '#dbeafe', text: '#1e3a8a', dot: '#3b82f6' },
  culture: { label: 'Culture', bg: '#ede9fe', text: '#4c1d95', dot: '#7c3aed' },
  walk:    { label: 'Nature',  bg: '#dcfce7', text: '#14532d', dot: '#16a34a' },
  food:    { label: 'Travel',  bg: '#fee2e2', text: '#7f1d1d', dot: '#ef4444' },
}

// ─── Marker helpers ────────────────────────────────────────────────────────────

function makeStayIcon(color: string) {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:20px;height:20px;border-radius:50%;
      background:${color};border:3px solid white;
      box-shadow:0 2px 8px rgba(0,0,0,0.4);
    "></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  })
}

function makeDestIcon(color: string) {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:12px;height:12px;border-radius:50%;
      background:${color};border:2px solid white;
      box-shadow:0 1px 4px rgba(0,0,0,0.35);
    "></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  })
}

function makeAirportIcon() {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:30px;height:30px;border-radius:8px;
      background:#1C1208;border:2.5px solid white;
      box-shadow:0 2px 8px rgba(0,0,0,0.5);
      display:flex;align-items:center;justify-content:center;
      font-size:15px;line-height:1;
    ">✈️</div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  })
}

const TYPE_COLOR: Record<ActivityType, string> = {
  beach:   '#f59e0b',
  boat:    '#3b82f6',
  culture: '#7c3aed',
  walk:    '#16a34a',
  food:    '#ef4444',
}

// ─── Map component ─────────────────────────────────────────────────────────────

interface MapViewProps {
  activeDayId: string | null
  onMapReady: (flyTo: (center: [number, number], zoom: number) => void) => void
}

function MapView({ activeDayId, onMapReady }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const markerLayersRef = useRef<Map<string, L.LayerGroup>>(new Map())

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const map = L.map(containerRef.current, {
      center: [40.8, 8.95],
      zoom: 8,
      zoomControl: true,
    })

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '© OpenStreetMap © CARTO',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map)

    // Add all markers & route lines per day
    STAYS.forEach(stay => {
      // Stay marker
      L.marker(stay.coords, { icon: makeStayIcon(stay.accent) })
        .addTo(map)
        .bindPopup(`<b>${stay.name}</b><br>${stay.nights} nights · ${stay.period}`)

      stay.days.forEach(day => {
        const group = L.layerGroup()

        day.destinations.forEach(dest => {
          const marker = L.marker(dest.coords, {
            icon: makeDestIcon(TYPE_COLOR[day.type]),
          }).bindPopup(`<b>${dest.name}</b><br>${dest.distance} · ${dest.time}<br><small>${dest.note}</small>`)
          group.addLayer(marker)

          // Dashed line from stay to destination
          const line = L.polyline([stay.coords, dest.coords], {
            color: stay.accent,
            weight: 1.5,
            opacity: 0.5,
            dashArray: '5 7',
          })
          group.addLayer(line)
        })

        group.addTo(map)
        markerLayersRef.current.set(day.id, group)
      })
    })

    // Airport — always visible, never dimmed
    L.marker(AIRPORT.coords, { icon: makeAirportIcon() })
      .addTo(map)
      .bindPopup(
        `<b>${AIRPORT.name}</b><br>` +
        `<b>→ ${AIRPORT.arrivalTo}:</b> ${AIRPORT.arrivalDistance} · ${AIRPORT.arrivalTime}<br>` +
        `<small>${AIRPORT.arrivalNote}</small>`
      )

    // Arrival route line (OLB → Cannigione)
    L.polyline([AIRPORT.coords, AIRPORT.arrivalCoords], {
      color: '#1d6b9e',
      weight: 2,
      opacity: 0.6,
      dashArray: '8 6',
    }).addTo(map).bindPopup(
      `<b>Arrival drive</b><br>${AIRPORT.arrivalDistance} · ${AIRPORT.arrivalTime}`
    )

    mapRef.current = map
    onMapReady((center, zoom) => map.flyTo(center, zoom, { duration: 1.4 }))

    return () => {
      map.remove()
      mapRef.current = null
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Dim non-active day markers when a day is selected
  useEffect(() => {
    markerLayersRef.current.forEach((group, dayId) => {
      group.eachLayer(layer => {
        const el = (layer as L.Marker).getElement?.()
        if (el) el.style.opacity = activeDayId && activeDayId !== dayId ? '0.25' : '1'
      })
    })
  }, [activeDayId])

  return (
    <div ref={containerRef} className="w-full rounded-xl overflow-hidden shadow-lg" style={{ height: 480 }} />
  )
}

// ─── Day card ─────────────────────────────────────────────────────────────────

interface DayCardProps {
  day: Day
  accent: string
  isActive: boolean
  onSelect: (day: Day) => void
}

function DayCard({ day, accent, isActive, onSelect }: DayCardProps) {
  const badge = ACTIVITY[day.type]

  return (
    <div
      onClick={() => onSelect(day)}
      className="cursor-pointer rounded-xl overflow-hidden shadow-sm border transition-all duration-200"
      style={{
        borderColor: isActive ? accent : '#e5e0d8',
        boxShadow: isActive ? `0 0 0 2px ${accent}40, 0 4px 16px ${accent}20` : undefined,
        background: '#fffef9',
      }}
    >
      {/* Accent top bar */}
      <div className="h-1" style={{ background: accent }} />

      <div className="p-4 sm:p-5">
        {/* Date row */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div
              className="flex flex-col items-center justify-center rounded-lg px-3 py-1.5 min-w-[52px]"
              style={{ background: `${accent}18` }}
            >
              <span className="text-[10px] font-semibold tracking-widest" style={{ color: accent }}>
                {day.shortDay}
              </span>
              <span className="text-2xl font-bold leading-none" style={{ color: accent }}>
                {day.dayNum}
              </span>
              <span className="text-[10px] font-semibold tracking-widest" style={{ color: accent }}>
                {day.month}
              </span>
            </div>
            <div>
              <div className="text-lg font-semibold leading-tight text-earth-dark">
                {day.emoji} {day.title}
              </div>
              <div className="text-xs text-earth-tan mt-0.5">{day.subtitle}</div>
            </div>
          </div>
          <span
            className="text-xs font-semibold px-2 py-1 rounded-full hidden sm:block"
            style={{ background: badge.bg, color: badge.text }}
          >
            {badge.label}
          </span>
        </div>

        {/* Destinations */}
        <div className="mb-3 rounded-lg overflow-hidden border border-earth-stone/30">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ background: `${accent}10` }}>
                <th className="text-left px-3 py-1.5 text-xs font-semibold text-earth-brown">Destination</th>
                <th className="text-right px-3 py-1.5 text-xs font-semibold text-earth-brown">Distance</th>
                <th className="text-right px-3 py-1.5 text-xs font-semibold text-earth-brown">Drive</th>
              </tr>
            </thead>
            <tbody>
              {day.destinations.map((dest, i) => (
                <tr key={i} className="border-t border-earth-stone/20">
                  <td className="px-3 py-2">
                    <div className="font-medium text-earth-dark text-sm">{dest.name}</div>
                    <div className="text-xs text-earth-tan mt-0.5">{dest.note}</div>
                  </td>
                  <td className="px-3 py-2 text-right text-earth-brown font-medium whitespace-nowrap text-xs">
                    {dest.distance}
                  </td>
                  <td className="px-3 py-2 text-right text-earth-brown font-medium whitespace-nowrap text-xs">
                    {dest.time}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Tips */}
        <ul className="space-y-1">
          {day.tips.map((tip, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-earth-brown">
              <span className="mt-0.5 shrink-0" style={{ color: accent }}>›</span>
              {tip}
            </li>
          ))}
        </ul>

        {/* Focus map button */}
        <button
          className="mt-3 text-xs font-semibold flex items-center gap-1 opacity-70 hover:opacity-100 transition-opacity"
          style={{ color: accent }}
          onClick={e => { e.stopPropagation(); onSelect(day) }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35M11 8v6M8 11h6"/>
          </svg>
          Focus on map
        </button>
      </div>
    </div>
  )
}

// ─── Arrival card ─────────────────────────────────────────────────────────────

function ArrivalCard({ onFocus }: { onFocus: () => void }) {
  return (
    <div
      className="rounded-xl overflow-hidden shadow-sm border border-earth-stone/40 mb-8"
      style={{ background: '#fffef9' }}
    >
      <div className="h-1" style={{ background: '#1C1208' }} />
      <div className="p-4 sm:p-5 flex items-start gap-4">
        <div className="text-3xl leading-none pt-0.5">✈️</div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-earth-dark">{AIRPORT.name}</div>
          <div className="text-xs text-earth-tan mb-3">June 26 arrival · pick up rental car here</div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-earth-tan text-xs">To</span>
              <span className="font-semibold text-earth-dark">{AIRPORT.arrivalTo}</span>
              <span className="text-earth-stone">·</span>
              <span className="text-earth-brown font-medium">{AIRPORT.arrivalDistance}</span>
              <span className="text-earth-stone">·</span>
              <span className="font-bold" style={{ color: '#1d6b9e' }}>{AIRPORT.arrivalTime}</span>
            </div>
          </div>
          <div className="text-xs text-earth-tan mt-1">{AIRPORT.arrivalNote}</div>
        </div>
        <button
          onClick={onFocus}
          className="text-xs font-semibold shrink-0 flex items-center gap-1 opacity-70 hover:opacity-100 transition-opacity"
          style={{ color: '#1d6b9e' }}
        >
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35M11 8v6M8 11h6"/>
          </svg>
          Map
        </button>
      </div>
    </div>
  )
}

// ─── Stay section ─────────────────────────────────────────────────────────────

interface StaySectionProps {
  stay: Stay
  activeDayId: string | null
  onDaySelect: (day: Day) => void
}

function StaySection({ stay, activeDayId, onDaySelect }: StaySectionProps) {
  return (
    <section className="mb-12">
      {/* Stay header */}
      <div className="flex items-center gap-4 mb-6">
        <div
          className="w-3 h-3 rounded-full shrink-0"
          style={{ background: stay.accent, boxShadow: `0 0 0 4px ${stay.accent}25` }}
        />
        <div>
          <h2 className="font-display text-2xl font-bold text-earth-dark">
            {stay.name}
          </h2>
          <div className="text-sm text-earth-tan">
            {stay.period} &nbsp;·&nbsp; {stay.nights} nights &nbsp;·&nbsp; {stay.region}
          </div>
        </div>
      </div>

      {/* Day cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {stay.days.map(day => (
          <DayCard
            key={day.id}
            day={day}
            accent={stay.accent}
            isActive={activeDayId === day.id}
            onSelect={onDaySelect}
          />
        ))}
      </div>
    </section>
  )
}

// ─── Trip stats bar ────────────────────────────────────────────────────────────

function TripStats() {
  const stats = [
    { label: 'Nights', value: '8' },
    { label: 'Bases', value: '2' },
    { label: 'Activities', value: '8 days' },
    { label: 'Total drive', value: '~450 km' },
    { label: 'Longest drive', value: '170 km' },
    { label: 'Flight', value: '20:40 Jul 3' },
  ]
  return (
    <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 mb-10">
      {stats.map(s => (
        <div key={s.label} className="rounded-xl text-center py-3 px-2" style={{ background: '#fffef9', border: '1px solid #e5e0d8' }}>
          <div className="font-display font-bold text-xl text-earth-dark leading-none">{s.value}</div>
          <div className="text-[11px] text-earth-tan mt-1 uppercase tracking-wide">{s.label}</div>
        </div>
      ))}
    </div>
  )
}

// ─── Tips section ─────────────────────────────────────────────────────────────

function GeneralTips() {
  const tips = [
    {
      icon: '☀️',
      title: 'Weather',
      items: ['Late June/early July: 28–34°C, essentially no rain', 'Sea temperature around 24–26°C — perfect for swimming', 'UV index very high — factor 50 and hat essential'],
    },
    {
      icon: '🚗',
      title: 'Driving',
      items: ['Rent a small car — parking in old towns is tight', 'Arrive at beaches before 9am in peak season', 'SS125 coastal road is spectacular but adds 30–40 min vs motorway'],
    },
    {
      icon: '🍽️',
      title: 'Food & Drink',
      items: ['Seafood is outstanding — order the catch of the day', 'Sardinian wines: Vermentino (white), Cannonau (red)', 'Lunch is the main meal; dinner is later (8:30–9pm)'],
    },
    {
      icon: '🏖️',
      title: 'Beaches',
      items: ['Most top beaches have limited parking — arrive early', 'Some beaches charge €5–10/day for parking in peak season', 'Bring your own snorkelling gear — rental is expensive'],
    },
  ]

  return (
    <section className="mt-12 pt-8 border-t border-earth-stone/30">
      <h2 className="font-display text-xl font-bold text-earth-dark mb-5">General Tips for Sardinia in Late June</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {tips.map(t => (
          <div key={t.title} className="rounded-xl p-4" style={{ background: '#fffef9', border: '1px solid #e5e0d8' }}>
            <div className="text-2xl mb-2">{t.icon}</div>
            <div className="font-semibold text-earth-dark mb-2">{t.title}</div>
            <ul className="space-y-1">
              {t.items.map((item, i) => (
                <li key={i} className="text-xs text-earth-brown flex gap-2">
                  <span className="text-earth-amber shrink-0 mt-0.5">›</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  )
}

// ─── Main app ─────────────────────────────────────────────────────────────────

export default function ItineraryApp() {
  const [activeDayId, setActiveDayId] = useState<string | null>(null)
  const flyToRef = useRef<((center: [number, number], zoom: number) => void) | null>(null)
  const mapSectionRef = useRef<HTMLDivElement>(null)

  const handleMapReady = useCallback((flyTo: (center: [number, number], zoom: number) => void) => {
    flyToRef.current = flyTo
  }, [])

  const handleDaySelect = useCallback((day: Day) => {
    setActiveDayId(prev => prev === day.id ? null : day.id)
    flyToRef.current?.(day.mapCenter, day.mapZoom)
    mapSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [])

  return (
    <div className="min-h-screen" style={{ background: '#f8f3e8' }}>
      {/* Header */}
      <header
        className="text-white py-12 px-6"
        style={{
          background: 'linear-gradient(135deg, #1C1208 0%, #2C4A2E 50%, #1d6b9e 100%)',
        }}
      >
        <div className="max-w-4xl mx-auto">
          <div className="text-xs font-semibold tracking-widest uppercase opacity-60 mb-2">Trip Planner</div>
          <h1 className="font-display text-4xl sm:text-5xl font-bold mb-2">Sardinia 2026</h1>
          <p className="text-lg opacity-80">June 26 – July 3 &nbsp;·&nbsp; 8 nights &nbsp;·&nbsp; Cannigione + Alghero</p>
          <p className="text-sm opacity-60 mt-3">
            One big activity per day · swim, walk, culture, boat · relaxed pace
          </p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        {/* Stats */}
        <TripStats />

        {/* Map */}
        <section ref={mapSectionRef} className="mb-10">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-display text-xl font-bold text-earth-dark">Map Overview</h2>
            {activeDayId && (
              <button
                onClick={() => {
                  setActiveDayId(null)
                  flyToRef.current?.([40.8, 8.95], 8)
                }}
                className="text-xs text-earth-tan hover:text-earth-dark transition-colors"
              >
                ← Show all
              </button>
            )}
          </div>
          <MapView activeDayId={activeDayId} onMapReady={handleMapReady} />
          <p className="text-xs text-earth-tan mt-2 text-center">
            Click a day card below to focus the map on that day's destinations
          </p>

          {/* Legend */}
          <div className="flex flex-wrap gap-3 mt-3 justify-center">
            <div className="flex items-center gap-1.5 text-xs text-earth-brown">
              <span className="inline-flex items-center justify-center w-4 h-4 rounded text-[9px]" style={{ background: '#1C1208', color: 'white' }}>✈</span>
              Olbia Airport
            </div>
            <div className="flex items-center gap-1.5 text-xs text-earth-brown">
              <span className="w-3 h-3 rounded-full" style={{ background: '#1d6b9e', border: '2px solid white' }} />
              Cannigione (Stay 1)
            </div>
            <div className="flex items-center gap-1.5 text-xs text-earth-brown">
              <span className="w-3 h-3 rounded-full" style={{ background: '#c0522b', border: '2px solid white' }} />
              Alghero (Stay 2)
            </div>
            {(Object.entries(ACTIVITY) as [ActivityType, typeof ACTIVITY[ActivityType]][]).map(([type, cfg]) => (
              <div key={type} className="flex items-center gap-1.5 text-xs text-earth-brown">
                <span className="w-2 h-2 rounded-full" style={{ background: TYPE_COLOR[type] }} />
                {cfg.label}
              </div>
            ))}
          </div>
        </section>

        {/* Arrival info */}
        <ArrivalCard
          onFocus={() => {
            flyToRef.current?.(AIRPORT.coords, 11)
            mapSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }}
        />

        {/* Itinerary by stay */}
        {STAYS.map(stay => (
          <StaySection
            key={stay.id}
            stay={stay}
            activeDayId={activeDayId}
            onDaySelect={handleDaySelect}
          />
        ))}

        {/* General tips */}
        <GeneralTips />
      </main>

      <footer className="text-center py-6 text-xs text-earth-tan border-t border-earth-stone/30 mt-4">
        Sardinia 2026 · Private trip planner · Have a wonderful vacation 🌊
      </footer>
    </div>
  )
}
