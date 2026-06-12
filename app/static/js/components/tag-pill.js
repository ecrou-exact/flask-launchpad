/**
 * tag-pill.js — Split-pill tag display component.
 *
 * Props:
 *   tag     : Object  { name, color, icon, source, namespace, is_active }
 *   size    : String  'sm' | '' | 'lg'  (default '')
 *
 * Displays: [icon | namespace/type] [label]
 * Text color auto-selected via YIQ for maximum contrast on the colored right side.
 */
const { computed } = Vue

function yiqTextColor(hex) {
    if (!hex) return '#ffffff'
    const h = hex.replace('#', '')
    if (h.length === 3) {
        const r = parseInt(h[0] + h[0], 16)
        const g = parseInt(h[1] + h[1], 16)
        const b = parseInt(h[2] + h[2], 16)
        return (r * 299 + g * 587 + b * 114) / 1000 >= 145 ? '#1a1a1a' : '#ffffff'
    }
    if (h.length >= 6) {
        const r = parseInt(h.slice(0, 2), 16)
        const g = parseInt(h.slice(2, 4), 16)
        const b = parseInt(h.slice(4, 6), 16)
        return (r * 299 + g * 587 + b * 114) / 1000 >= 145 ? '#1a1a1a' : '#ffffff'
    }
    return '#ffffff'
}

function hslTextColor(hsl) {
    // Rough brightness from HSL lightness
    const m = hsl.match(/hsl\(\d+\.?\d*,\s*\d+%,\s*(\d+)%\)/)
    if (m) return parseInt(m[1]) >= 65 ? '#1a1a1a' : '#ffffff'
    return '#ffffff'
}

function resolveTextColor(color) {
    if (!color) return '#ffffff'
    if (color.startsWith('#')) return yiqTextColor(color)
    if (color.startsWith('hsl')) return hslTextColor(color)
    return '#ffffff'
}

function parseTagDisplay(tag) {
    if (!tag) return { left: '', right: '' }
    const name = tag.name || ''

    // "namespace:predicate=\"value\"" → left=namespace, right=value
    // "namespace:predicate"           → left=namespace, right=predicate
    const colonIdx = name.indexOf(':')
    if (colonIdx === -1) return { left: tag.source || 'tag', right: name }

    const ns    = name.slice(0, colonIdx)
    const rest  = name.slice(colonIdx + 1)
    const eqIdx = rest.indexOf('="')
    const label = eqIdx !== -1 ? rest.slice(eqIdx + 2).replace(/"$/, '') : rest

    return { left: ns, right: label }
}

const TagPill = {
    name: 'TagPill',
    template: `
        <span
            class="tag-pill"
            :class="[size ? 'tag-pill--' + size : '', !tag.is_active ? 'tag-pill--inactive' : '']"
            :title="tag.name + (tag.description ? '\\n' + tag.description : '')"
        >
            <span class="tag-pill-left">
                <i :class="iconClass"></i>
                {{ display.left }}
            </span>
            <span class="tag-pill-right" :style="rightStyle">
                <span>{{ display.right }}</span>
            </span>
        </span>
    `,
    props: {
        tag:  { type: Object, required: true },
        size: { type: String, default: '' },
    },
    setup(props) {
        const display = computed(() => parseTagDisplay(props.tag))

        const iconClass = computed(() => {
            const src = props.tag.source || 'custom'
            const icons = {
                custom:        'fas fa-tag',
                taxonomy:      'fas fa-sitemap',
                galaxy:        'fas fa-globe',
                vulnerability: 'fas fa-bug',
            }
            return props.tag.icon || icons[src] || 'fas fa-tag'
        })

        const rightStyle = computed(() => {
            const color = props.tag.color || '#6c757d'
            return {
                backgroundColor: color,
                color:           resolveTextColor(color),
            }
        })

        return { display, iconClass, rightStyle }
    },
}

export { TagPill, yiqTextColor, parseTagDisplay }
export default TagPill
