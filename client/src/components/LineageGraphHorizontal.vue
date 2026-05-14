<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import DataCommitNode from './DataCommitNode.vue'
import ModelRunNode from './ModelRunNode.vue'

const props = defineProps({
  dataCommits: {
    type: Array,
    required: true,
  },
  modelRuns: {
    type: Array,
    required: true,
  },
  connections: {
    type: Object,
    required: true,
  },
})

// Active nodes for highlighting
const activeDataNodes = ref(new Set())
const activeModelNodes = ref(new Set())

// SVG for connections
const svgPaths = ref([])
const svgLines = ref([])
const graphContainer = ref(null)
const svgElement = ref(null)

// Group model runs by data commit
const modelRunsByDataCommit = computed(() => {
  const grouped = {}

  props.dataCommits.forEach(commit => {
    grouped[commit.id] = props.modelRuns.filter(run =>
      run.dataCommitId === commit.id
    )
  })

  return grouped
})

// Handle node hover
function handleDataNodeHover(nodeId, isHovering) {
  if (isHovering) {
    activeDataNodes.value.add(nodeId)
    const connectedModels = props.connections[nodeId] || []
    connectedModels.forEach(modelId => activeModelNodes.value.add(modelId))
  } else {
    activeDataNodes.value.clear()
    activeModelNodes.value.clear()
  }
  drawConnections()
}

function handleModelNodeHover(nodeId, isHovering) {
  if (isHovering) {
    activeModelNodes.value.add(nodeId)
    Object.keys(props.connections).forEach(dataId => {
      if (props.connections[dataId].includes(nodeId)) {
        activeDataNodes.value.add(dataId)
      }
    })
  } else {
    activeDataNodes.value.clear()
    activeModelNodes.value.clear()
  }
  drawConnections()
}

// Get node position
function getNodePosition(nodeId, position = 'center') {
  const node = document.querySelector(`[data-id="${nodeId}"]`)
  if (!node || !graphContainer.value) return null

  const nodeRect = node.getBoundingClientRect()
  const containerRect = graphContainer.value.getBoundingClientRect()

  const x = nodeRect.left - containerRect.left + nodeRect.width / 2
  const y = nodeRect.top - containerRect.top

  if (position === 'top') {
    return { x, y }
  } else if (position === 'bottom') {
    return { x, y: y + nodeRect.height }
  }
  return { x, y: y + nodeRect.height / 2 }
}

// Draw SVG connection lines
function drawConnections() {
  if (!graphContainer.value || !svgElement.value) return

  const paths = []
  const lines = []
  const containerRect = graphContainer.value.getBoundingClientRect()

  svgElement.value.setAttribute('width', containerRect.width)
  svgElement.value.setAttribute('height', containerRect.height)

  // Draw horizontal timeline between data commits
  if (props.dataCommits.length > 1) {
    for (let i = 0; i < props.dataCommits.length - 1; i++) {
      const current = getNodePosition(props.dataCommits[i].id, 'center')
      const next = getNodePosition(props.dataCommits[i + 1].id, 'center')

      if (current && next) {
        lines.push({
          x1: current.x + 140, // Offset from node edge
          y1: current.y,
          x2: next.x - 140,
          y2: next.y,
          type: 'timeline',
          hasArrow: true
        })
      }
    }
  }

  // Draw single vertical line from each data commit to first model run
  Object.keys(props.connections).forEach(dataId => {
    const dataBottom = getNodePosition(dataId, 'bottom')
    if (!dataBottom) return

    // Check if this data commit has any connected model runs
    const connectedRuns = props.connections[dataId]
    if (connectedRuns.length > 0) {
      // Get the position of the first model run
      const firstModelId = connectedRuns[0]
      const firstModelTop = getNodePosition(firstModelId, 'top')

      if (firstModelTop) {
        const isActive = activeDataNodes.value.has(dataId)

        // Draw line from data commit bottom to first model run top
        lines.push({
          x1: dataBottom.x,
          y1: dataBottom.y,
          x2: dataBottom.x,
          y2: firstModelTop.y,
          type: 'connection',
          active: isActive,
          best: false
        })
      }
    }
  })

  svgLines.value = lines
}

// Debounce helper
function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

const debouncedRedraw = debounce(drawConnections, 150)

onMounted(async () => {
  await nextTick()
  setTimeout(drawConnections, 100)
  window.addEventListener('resize', debouncedRedraw)
})
</script>

<template>
  <div ref="graphContainer" class="lineage-graph-horizontal">
    <!-- SVG for connections -->
    <svg
      ref="svgElement"
      class="connections"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="10"
          refX="9"
          refY="3"
          orient="auto"
        >
          <polygon
            points="0 0, 10 3, 0 6"
            fill="rgba(139, 92, 246, 0.6)"
          />
        </marker>
      </defs>

      <line
        v-for="(line, index) in svgLines"
        :key="index"
        :x1="line.x1"
        :y1="line.y1"
        :x2="line.x2"
        :y2="line.y2"
        :class="{
          'timeline-line': line.type === 'timeline',
          'connection-line': line.type === 'connection',
          'active': line.active,
          'best': line.best
        }"
        :marker-end="line.hasArrow ? 'url(#arrowhead)' : ''"
      />
    </svg>

    <!-- Horizontal Layout -->
    <div class="graph-layout">
      <!-- Top: Data Commits -->
      <section class="data-branch">
        <h2 class="branch-label">Data Evolution</h2>
        <div class="data-timeline">
          <DataCommitNode
            v-for="commit in dataCommits"
            :key="commit.id"
            :commit="commit"
            :active="activeDataNodes.has(commit.id)"
            @hover="handleDataNodeHover"
          />
        </div>
      </section>

      <!-- Bottom: Model Runs -->
      <section class="model-branch">
        <h2 class="branch-label">Model Runs</h2>
        <div class="model-columns">
          <div
            v-for="commit in dataCommits"
            :key="`models-${commit.id}`"
            class="model-column"
          >
            <div class="model-runs-vertical">
              <ModelRunNode
                v-for="run in modelRunsByDataCommit[commit.id]"
                :key="run.id"
                :run="run"
                :active="activeModelNodes.has(run.id)"
                @hover="handleModelNodeHover"
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.lineage-graph-horizontal {
  position: relative;
  min-height: 600px;
  width: 100%;
  padding: 24px;
}

/* SVG Connections */
.connections {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.timeline-line {
  stroke: rgba(139, 92, 246, 0.6);
  stroke-width: 2;
}

.connection-line {
  stroke: rgba(139, 92, 246, 0.3);
  stroke-width: 2;
  transition: all 0.2s;
}

.connection-line.active {
  stroke: var(--accent-purple);
  stroke-width: 3;
  opacity: 1;
}

.connection-line.best {
  stroke: var(--accent-green);
  stroke-width: 3;
  opacity: 0.8;
}

/* Graph Layout */
.graph-layout {
  display: flex;
  flex-direction: column;
  gap: 100px;
  position: relative;
  z-index: 2;
}

.branch-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-tertiary);
  margin-bottom: 24px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Data Branch */
.data-branch {
  width: 100%;
}

.data-timeline {
  display: flex;
  gap: 80px;
  justify-content: flex-start;
  padding-bottom: 16px;
}

/* Model Branch */
.model-branch {
  width: 100%;
}

.model-columns {
  display: flex;
  gap: 80px;
  align-items: flex-start;
}

.model-column {
  flex: 0 0 280px;
  width: 280px;
}

.model-runs-vertical {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
