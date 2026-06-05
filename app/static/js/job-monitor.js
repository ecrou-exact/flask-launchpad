/**
 * job-monitor.js — Global floating job progress widget.
 * Mounts on #job-monitor-widget as its own Vue app (separate from page apps).
 * Polls /api/jobs/ for active jobs; persists across navigation via sessionStorage.
 */

const { createApp, ref, computed, onMounted, onUnmounted, nextTick } = Vue

const ACTIVE_STATUSES = ['pending', 'running', 'paused']
const DISMISS_KEY     = 'jm_dismissed_at'
const POLL_ACTIVE_MS  = 2500
const POLL_IDLE_MS    = 5000

function apiFetch(url, method = 'GET', body = null) {
    const csrf = document.getElementById('csrf_token')?.value || ''
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    }
    if (body !== null) opts.body = JSON.stringify(body)
    return fetch(url, opts)
}

createApp({
    delimiters: ['[[', ']]'],
    setup() {
        const jobs      = ref([])
        const expanded  = ref(false)
        const visible   = ref(false)
        const animating = ref(false)   // true while fade-out plays

        let   pollTimer  = null
        let   dismissed  = false

        // ── helpers ────────────────────────────────────────────────────────────

        function getDismissedAt() {
            const v = sessionStorage.getItem(DISMISS_KEY)
            return v ? parseInt(v, 10) : 0
        }

        function markDismissed() {
            sessionStorage.setItem(DISMISS_KEY, Date.now())
            dismissed = true
        }

        function hasNewJobSinceDismiss(jobList) {
            const ts = getDismissedAt()
            if (!ts) return true
            return jobList.some(j => new Date(j.created_at).getTime() > ts)
        }

        // ── polling ────────────────────────────────────────────────────────────

        async function poll() {
            try {
                const res = await apiFetch('/api/jobs/?status=active&per_page=20')
                if (!res.ok) return
                const data    = await res.json()
                const active  = (data.items || []).filter(j => ACTIVE_STATUSES.includes(j.status))

                if (active.length === 0) {
                    if (visible.value) hide()
                    jobs.value = []
                    schedulePoll(POLL_IDLE_MS)
                    return
                }

                // Merge logs — keep existing log arrays, only update progress/status
                const prev = Object.fromEntries(jobs.value.map(j => [j.uuid, j]))
                jobs.value = active.map(j => ({
                    ...j,
                    // Keep expanded log state from previous fetch
                    _logs: prev[j.uuid]?._logs ?? (j.logs || []).slice(-5),
                }))

                // Fetch fresh logs for running jobs (last 5 lines)
                for (const j of jobs.value) {
                    if (j.logs && j.logs.length) {
                        j._logs = j.logs.slice(-5)
                    }
                }

                // Decide whether to show
                if (!dismissed && hasNewJobSinceDismiss(active)) {
                    if (!visible.value && !animating.value) show()
                }

                schedulePoll(POLL_ACTIVE_MS)
            } catch (_) {
                schedulePoll(POLL_IDLE_MS)
            }
        }

        function schedulePoll(delay) {
            clearTimeout(pollTimer)
            pollTimer = setTimeout(poll, delay)
        }

        // ── visibility ────────────────────────────────────────────────────────

        function show() {
            dismissed   = false
            visible.value = true
        }

        function hide() {
            animating.value = true
            setTimeout(() => {
                visible.value   = false
                animating.value = false
            }, 200)
        }

        function dismiss() {
            markDismissed()
            hide()
        }

        function toggleExpand() {
            expanded.value = !expanded.value
        }

        // ── computed ──────────────────────────────────────────────────────────

        const firstJob = computed(() => jobs.value[0] || null)
        const extraCount = computed(() => Math.max(0, jobs.value.length - 1))

        function progressPct(job) {
            return job.progress ?? 0
        }

        function statusLabel(job) {
            return job.status
        }

        function logClass(entry) {
            const lvl = (entry.level || '').toLowerCase()
            if (lvl === 'error')   return 'jm-log-line--error'
            if (lvl === 'warning') return 'jm-log-line--warning'
            if (lvl === 'success') return 'jm-log-line--success'
            return ''
        }

        // ── lifecycle ─────────────────────────────────────────────────────────

        onMounted(() => {
            poll()
        })

        onUnmounted(() => {
            clearTimeout(pollTimer)
        })

        return {
            jobs, expanded, visible, animating,
            firstJob, extraCount,
            progressPct, statusLabel, logClass,
            dismiss, toggleExpand,
        }
    },

    template: `
<div v-if="visible || animating" :class="['jm-panel', { 'jm-out': animating }]">

    <!-- Header -->
    <div class="jm-header" @click="toggleExpand">
        <i class="fas fa-gear jm-spinner"></i>
        <span class="jm-title">
            [[ jobs.length ]] job[[ jobs.length !== 1 ? 's' : '' ]] active
        </span>
        <button class="jm-expand-btn" title="Toggle details" @click.stop="toggleExpand">
            <i :class="expanded ? 'fas fa-chevron-down' : 'fas fa-chevron-up'"></i>
        </button>
        <button class="jm-close-btn" title="Dismiss" @click.stop="dismiss">
            <i class="fas fa-xmark"></i>
        </button>
    </div>

    <!-- Collapsed: first job summary -->
    <div v-if="!expanded && firstJob" class="jm-summary">
        <div class="jm-summary-title">[[ firstJob.title ]]</div>
        <div class="jm-progress-track">
            <div class="jm-progress-fill"
                 :class="firstJob.status === 'pending' ? 'jm-progress-fill--indeterminate' : ''"
                 :style="{ width: firstJob.status !== 'pending' ? progressPct(firstJob) + '%' : '' }">
            </div>
        </div>
        <div class="jm-summary-meta">
            <span>[[ statusLabel(firstJob) ]]</span>
            <span v-if="firstJob.status !== 'pending'">[[ progressPct(firstJob) ]]%</span>
        </div>
    </div>

    <!-- Expanded: all jobs -->
    <div v-if="expanded" class="jm-body">
        <div v-for="job in jobs" :key="job.uuid" class="jm-job-item">
            <div class="jm-job-header">
                <span class="jm-job-title" :title="job.title">[[ job.title ]]</span>
                <span class="jm-job-status" :class="'jm-job-status--' + job.status">
                    [[ job.status ]]
                </span>
                <a :href="'/jobs/' + job.uuid" target="_blank" class="jm-job-link" title="View detail">
                    <i class="fas fa-arrow-up-right-from-square"></i>
                </a>
            </div>
            <div class="jm-progress-track">
                <div class="jm-progress-fill"
                     :class="job.status === 'pending' ? 'jm-progress-fill--indeterminate' : ''"
                     :style="{ width: job.status !== 'pending' ? progressPct(job) + '%' : '' }">
                </div>
            </div>
            <div v-if="job._logs && job._logs.length" class="jm-logs">
                <p v-for="(entry, i) in job._logs" :key="i"
                   class="jm-log-line" :class="logClass(entry)">
                    [[ entry.msg ]]
                </p>
            </div>
        </div>
    </div>

    <!-- Footer when collapsed with multiple jobs -->
    <div v-if="!expanded && extraCount > 0" class="jm-footer">
        + [[ extraCount ]] more job[[ extraCount !== 1 ? 's' : '' ]]
    </div>

</div>
`,
}).mount('#job-monitor-widget')
