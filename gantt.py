import streamlit as st
import streamlit.components.v1 as components
import json
from datetime import datetime

# Set the Streamlit page configuration to use the "wide" layout.
st.set_page_config(layout="wide", page_title="Gantt Chart Project Manager")

# Initialize session state
if 'gantt_data' not in st.session_state:
    st.session_state.gantt_data = {
        'tasks': [],
        'projectGroups': [],
        'projectTitle': 'Project Timeline',
        'projectSubtitle': 'Interactive Gantt Chart'
    }

# Main title
st.title("🚀 Gantt Chart Project Manager")
st.markdown("---")

# Gantt Chart HTML Component
gantt_chart_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gantt Chart</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --group-width: 150px;
            --task-name-width: 250px;
            --deps-width: 100px;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            overflow: hidden;
        }}
        .main-container {{
            height: 95vh;
            display: flex;
            flex-direction: column;
        }}
        .gantt-chart-container {{
            flex-grow: 1;
            overflow: auto;
        }}
        #gantt-chart {{
            display: inline-grid;
        }}
        .gantt-chart-container::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        .gantt-chart-container::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 10px;
        }}
        .gantt-chart-container::-webkit-scrollbar-thumb {{
            background: #ccc;
            border-radius: 10px;
        }}
        .gantt-chart-container::-webkit-scrollbar-thumb:hover {{
            background: #aaa;
        }}
        .gantt-tooltip {{
            visibility: hidden;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        .gantt-bar-wrapper:hover .gantt-tooltip {{
            visibility: visible;
            opacity: 1;
        }}
        input[type="range"]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            background: #006152;
            cursor: pointer;
            border-radius: 50%;
        }}
        input[type="range"]::-moz-range-thumb {{
            width: 20px;
            height: 20px;
            background: #006152;
            cursor: pointer;
            border-radius: 50%;
        }}

        #dependency-lines {{
            position: absolute;
            top: 0;
            left: 0;
            pointer-events: none;
            overflow: visible;
            z-index: 5;
        }}

        .gantt-bar-handle {{
            position: absolute;
            top: 0;
            height: 100%;
            width: 8px;
            cursor: ew-resize;
            z-index: 10;
        }}
        .gantt-bar-handle.left {{ left: -4px; }}
        .gantt-bar-handle.right {{ right: -4px; }}
        .gantt-bar-bg {{ cursor: grab; }}
        .gantt-bar-bg:active {{ cursor: grabbing; }}

        .resizer {{
            position: absolute;
            top: 0;
            right: 0;
            width: 5px;
            height: 100%;
            cursor: col-resize;
            user-select: none;
            z-index: 40;
        }}

        @media print {{
            @page {{
                size: A3 landscape;
                margin: 1cm;
            }}
            * {{
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
                box-shadow: none !important;
            }}
            body {{ padding: 0 !important; margin: 0 !important; background-color: #fff !important; overflow: visible; }}
            .main-container {{ height: auto; }}
            header > div:last-child, footer, #task-modal, #group-modal, .gantt-tooltip, .gantt-bar-handle, .resizer, #dependency-modal {{
                display: none !important;
            }}
            .max-w-7xl {{ margin: 0 !important; max-width: 100% !important; border: none !important; overflow: visible !important; }}
            header {{ border-bottom: 2px solid #ccc !important; justify-content: flex-start !important; }}
            #project-title, #project-subtitle {{ color: #000 !important; }}
            .gantt-chart-container {{
                overflow: visible !important;
                padding: 0 !important;
                border: 1px solid #eee;
            }}
            .sticky {{ position: static !important; }}
            #dependency-lines {{ display: block !important; position: absolute !important; }}
        }}
    </style>
</head>
<body class="bg-gray-100 p-4 sm:p-6 lg:p-8">

    <div class="max-w-7xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden main-container">
        <header class="p-5 text-white flex justify-between items-center flex-wrap gap-4" style="background-color: #006152;">
            <div>
                <input type="text" id="project-title" value="{st.session_state.gantt_data['projectTitle']}" class="text-2xl font-bold bg-transparent border-none text-white w-full focus:outline-none focus:ring-1 focus:ring-white/50 rounded-md p-1 -m-1">
                <input type="text" id="project-subtitle" value="{st.session_state.gantt_data['projectSubtitle']}" class="text-sm opacity-90 bg-transparent border-none text-white w-full focus:outline-none focus:ring-1 focus:ring-white/50 rounded-md p-1 -m-1 mt-1">
            </div>
            <div class="flex items-center gap-2 flex-wrap">
                 <button id="manage-groups-btn" class="px-3 py-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors text-sm focus:outline-none focus:ring-2 focus:ring-white">Manage Groups</button>
                <select id="view-mode" class="bg-white/20 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-white">
                    <option value="day" class="text-black">Days</option>
                    <option value="week" class="text-black">Weeks</option>
                    <option value="month" class="text-black">Months</option>
                    <option value="quarter" class="text-black">Quarters</option>
                    <option value="year" class="text-black">Years</option>
                </select>
                <label for="file-input" class="cursor-pointer p-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors focus:outline-none focus:ring-2 focus:ring-white" title="Upload Excel">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd" /></svg>
                </label>
                <input type="file" id="file-input" class="hidden" accept=".xlsx, .xls">
                <button id="download-btn" title="Download Excel" class="p-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors focus:outline-none focus:ring-2 focus:ring-white">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
                </button>
                 <button id="clear-data-btn" title="Clear All Local Data" class="p-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors focus:outline-none focus:ring-2 focus:ring-white">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm4 0a1 1 0 012 0v6a1 1 0 11-2 0V8z" clip-rule="evenodd" />
                    </svg>
                </button>
                <button id="download-html-btn" title="Download as HTML" class="p-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors focus:outline-none focus:ring-2 focus:ring-white">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clip-rule="evenodd" />
                    </svg>
                </button>
                 <button id="print-btn" title="Print to PDF" class="p-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors focus:outline-none focus:ring-2 focus:ring-white">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5 4v3H4a2 2 0 00-2 2v6a2 2 0 002 2h12a2 2 0 002-2V9a2 2 0 00-2-2h-1V4a2 2 0 00-2-2H7a2 2 0 00-2 2zm8 0H7v3h6V4zm0 8H7v4h6v-4z" clip-rule="evenodd" /></svg>
                </button>
                <button id="add-task-btn" class="px-4 py-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors focus:outline-none focus:ring-2 focus:ring-white">
                    + Add Task
                </button>
            </div>
        </header>

        <div id="gantt-chart-container" class="gantt-chart-container relative">
            <div id="gantt-chart" class="relative"></div>
            <svg id="dependency-lines"></svg>
        </div>
         <footer class="p-4 bg-gray-50 border-t border-gray-200 text-xs text-gray-500 text-center">
            <p>Generated on: <span id="current-date">{datetime.now().strftime("%Y-%m-%d %H:%M")}</span></p>
            <p class="mt-1">Created by Dave Maher</p>
        </footer>
    </div>
    
    <!-- Modals -->
    <div id="group-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <h2 class="text-xl font-bold text-gray-800 mb-4">Manage Groups</h2>
            <div id="group-list" class="mb-4 max-h-60 overflow-y-auto pr-2 space-y-2"></div>
            <form id="add-group-form" class="mt-4 border-t pt-4">
                <p class="text-sm font-medium text-gray-700 mb-2">Add New Group</p>
                <div class="flex items-center gap-3">
                    <input type="text" id="new-group-name" placeholder="Group Name" class="flex-grow p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500" required>
                    <input type="color" id="new-group-color" value="#79D3C9" class="w-10 h-10 p-1 border border-gray-300 rounded-lg">
                    <button type="submit" class="px-4 py-2 text-white rounded-lg" style="background-color: #006152;">Add</button>
                </div>
            </form>
            <div class="flex justify-end mt-6">
                <button type="button" id="close-group-modal-btn" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300">Done</button>
            </div>
        </div>
    </div>
    <div id="task-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <h2 id="modal-title" class="text-xl font-bold text-gray-800 mb-6">Add New Task</h2>
            <form id="task-form">
                <input type="hidden" id="task-id">
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div>
                         <label for="task-group" class="block text-sm font-medium text-gray-700 mb-1">Group</label>
                         <select id="task-group" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"></select>
                    </div>
                    <div>
                        <label for="task-name" class="block text-sm font-medium text-gray-700 mb-1">Task Name</label>
                        <input type="text" id="task-name" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500" required>
                    </div>
                </div>
                <div class="mb-4">
                    <label for="task-dependencies" class="block text-sm font-medium text-gray-700 mb-1">Dependencies</label>
                    <select id="task-dependencies" multiple class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 h-24"></select>
                </div>
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <label for="task-start" class="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                        <input type="date" id="task-start" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500" required>
                    </div>
                    <div>
                        <label for="task-end" class="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                        <input type="date" id="task-end" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500" required>
                    </div>
                </div>
                <div class="flex items-center gap-4 mb-6">
                    <div class="flex-grow">
                        <label for="task-progress" class="block text-sm font-medium text-gray-700 mb-1">Progress (<span id="progress-value">0</span>%)</label>
                        <input type="range" id="task-progress" min="0" max="100" value="0" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
                    </div>
                    <div>
                         <label for="task-color" class="block text-sm font-medium text-gray-700 mb-1">Color</label>
                        <input type="color" id="task-color" value="#25B8A3" class="w-10 h-10 p-1 border border-gray-300 rounded-lg disabled:opacity-50">
                    </div>
                </div>
                <div class="flex justify-end gap-3">
                    <button type="button" id="delete-task-btn" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50 hidden mr-auto">Delete</button>
                    <button type="button" id="cancel-btn" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-opacity-50">Cancel</button>
                    <button type="submit" id="save-task-btn" class="px-4 py-2 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-opacity-50" style="background-color: #006152; hover:background-color: #004c40;">Save Task</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Dependency Confirmation Modal -->
    <div id="dependency-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <h2 class="text-xl font-bold text-gray-800 mb-4">Update Dependent Tasks?</h2>
            <p id="dependency-modal-text" class="text-sm text-gray-600 mb-4">Changing this task's dates will affect the following dependent tasks. Do you want to automatically shift their dates?</p>
            <div id="dependent-tasks-list" class="mb-4 max-h-40 overflow-y-auto pr-2 space-y-2">
                <!-- Dependent tasks will be listed here -->
            </div>
            <div class="flex justify-end gap-3 mt-6">
                <button type="button" id="cancel-dependency-update" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300">Cancel</button>
                <button type="button" id="confirm-dependency-update" class="px-4 py-2 text-white rounded-lg" style="background-color: #006152;">Yes, Update</button>
            </div>
        </div>
    </div>

    <script>
        // Initial state from Streamlit
        const initialState = {json.dumps(st.session_state.gantt_data)};
        
        document.addEventListener('DOMContentLoaded', () => {
            // --- STATE & CONFIGURATION ---
            let viewMode = 'day'; 
            let tasks = initialState.tasks || []; 
            let projectGroups = initialState.projectGroups || [];
            let columnWidths = {{
                group: 150,
                taskName: 250,
                deps: 100
            }};

            // Chart dimensions
            let chartStartDate = null;
            let pixelsPerDay = 0;
            let taskRowHeight = 40;

            // Drag states
            let isDragging = false;
            let currentTaskId = null;
            let dragStartPos = 0;
            let dragType = 'move';
            let originalTaskData = null;
            let dragStartStyles = null;
            let isResizing = false;
            let resizingColumn = null;

            // --- DOM ELEMENTS ---
            const ganttChartContainerEl = document.getElementById('gantt-chart-container');
            const ganttChartEl = document.getElementById('gantt-chart');
            const dependencyLinesEl = document.getElementById('dependency-lines');
            const currentDateEl = document.getElementById('current-date');
            const addTaskBtn = document.getElementById('add-task-btn');
            const taskModal = document.getElementById('task-modal');
            const taskForm = document.getElementById('task-form');
            const cancelBtn = document.getElementById('cancel-btn');
            const deleteTaskBtn = document.getElementById('delete-task-btn');
            const downloadBtn = document.getElementById('download-btn');
            const downloadHtmlBtn = document.getElementById('download-html-btn');
            const clearDataBtn = document.getElementById('clear-data-btn');
            const printBtn = document.getElementById('print-btn');
            const fileInput = document.getElementById('file-input');
            const projectTitleEl = document.getElementById('project-title');
            const projectSubtitleEl = document.getElementById('project-subtitle');
            const viewModeSelect = document.getElementById('view-mode');
            const manageGroupsBtn = document.getElementById('manage-groups-btn');
            const groupModal = document.getElementById('group-modal');
            const closeGroupModalBtn = document.getElementById('close-group-modal-btn');
            const addGroupForm = document.getElementById('add-group-form');
            const groupListEl = document.getElementById('group-list');
            const dependencyModal = document.getElementById('dependency-modal');
            const dependencyModalText = document.getElementById('dependency-modal-text');
            const dependentTasksListEl = document.getElementById('dependent-tasks-list');
            const confirmDependencyUpdateBtn = document.getElementById('confirm-dependency-update');
            const cancelDependencyUpdateBtn = document.getElementById('cancel-dependency-update');

            // --- UTILITY FUNCTIONS ---
            const formatDateToDDMMYYYY = (date) => {{
                if (!date || isNaN(date.getTime())) return '';
                const day = String(date.getUTCDate()).padStart(2, '0');
                const month = String(date.getUTCMonth() + 1).padStart(2, '0');
                const year = date.getUTCFullYear();
                return `${{day}}/${{month}}/${{year}}`;
            }};

            const formatDateToYYYYMMDD = (date) => {{
                if (!date || isNaN(date.getTime())) return '';
                return date.toISOString().slice(0, 10);
            }};

            const parseDate = (dateStr) => {{
                if (!dateStr) return null;
                if (dateStr instanceof Date) {{
                    return new Date(Date.UTC(dateStr.getFullYear(), dateStr.getMonth(), dateStr.getDate()));
                }}
                if (typeof dateStr !== 'string') return null;

                const partsDMY = dateStr.split('/');
                if (partsDMY.length === 3) {{
                    const [day, month, year] = partsDMY.map(Number);
                    if (year > 1000 && month >= 1 && month <= 12 && day >= 1 && day <= 31) {{
                        return new Date(Date.UTC(year, month - 1, day));
                    }}
                }}
                const partsYMD = dateStr.split('-');
                if (partsYMD.length === 3) {{
                    const [year, month, day] = partsYMD.map(Number);
                    if (year > 1000 && month >= 1 && month <= 12 && day >= 1 && day <= 31) {{
                        return new Date(Date.UTC(year, month - 1, day));
                    }}
                }}
                return null;
            }};

            const addDays = (date, days) => {{
                const result = new Date(date);
                result.setUTCDate(result.getUTCDate() + days);
                return result;
            }};

            const dayDiff = (startDateStr, endDateStr) => {{
                const msPerDay = 1000 * 60 * 60 * 24;
                const start = parseDate(startDateStr);
                const end = parseDate(endDateStr);
                if (!start || !end) return 0;
                return Math.round((end - start) / msPerDay + 0.00001);
            }};

            const showToast = (message, isError = false, needsConfirmation = false) => {{
                const toastId = 'gantt-toast';
                document.getElementById(toastId)?.remove();
                const toast = document.createElement('div');
                toast.id = toastId;
                toast.className = `fixed bottom-5 right-5 p-4 rounded-lg shadow-lg text-white z-50 transform translate-y-20 opacity-0 transition-all duration-300`;
                toast.textContent = message;
                let bgColor = isError ? 'bg-red-600' : 'bg-green-600';
                if (needsConfirmation) bgColor = 'bg-yellow-600';
                toast.classList.add(bgColor);
                document.body.appendChild(toast);
                setTimeout(() => toast.classList.remove('translate-y-20', 'opacity-0'), 10);
                setTimeout(() => {{
                    toast.classList.add('translate-y-20', 'opacity-0');
                    setTimeout(() => toast.remove(), 300);
                }}, 3000);
            }};

            // --- STATE MANAGEMENT ---
            const saveState = () => {{
                try {{
                    const state = {{
                        tasks,
                        projectGroups,
                        viewMode,
                        projectTitle: projectTitleEl.value,
                        projectSubtitle: projectSubtitleEl.value,
                        columnWidths,
                    }};
                    // Send to Streamlit
                    if (window.parent && window.parent.postMessage) {{
                        window.parent.postMessage({{
                            type: 'GANTT_CHART_UPDATE',
                            data: state
                        }}, '*');
                    }}
                }} catch (e) {{ console.error("Failed to save state", e); }}
            }};
            
            const clearState = () => {{
                showToast("Are you sure? This will delete all data. Click again to confirm.", false, true);
                clearDataBtn.onclick = () => {{
                    tasks = [];
                    projectGroups = [];
                    projectTitleEl.value = "Project Timeline";
                    projectSubtitleEl.value = "Interactive Gantt Chart";
                    viewMode = 'day';
                    viewModeSelect.value = 'day';
                    columnWidths = {{ group: 150, taskName: 250, deps: 100 }};
                    renderGanttChart();
                    saveState();
                    showToast("All data has been cleared.");
                    clearDataBtn.onclick = clearState;
                }};
                setTimeout(() => {{ clearDataBtn.onclick = clearState; }}, 3000);
            }};

            // --- DEPENDENCY LOGIC ---
            const showDependencyModal = (updatePlan, text, onConfirm, onCancel) => {{
                dependencyModalText.textContent = text;
                dependentTasksListEl.innerHTML = updatePlan.map(d => `<p class="p-2 bg-gray-100 rounded-md">#${{d.id}}: ${{d.name}}</p>`).join('');
                dependencyModal.classList.remove('hidden');
                dependencyModal.classList.add('flex');

                const cleanup = () => {{
                    dependencyModal.classList.add('hidden');
                    dependencyModal.classList.remove('flex');
                    confirmDependencyUpdateBtn.removeEventListener('click', confirmHandler);
                    cancelDependencyUpdateBtn.removeEventListener('click', cancelHandler);
                }};

                const confirmHandler = () => {{
                    cleanup();
                    onConfirm();
                }};
                const cancelHandler = () => {{
                    cleanup();
                    onCancel();
                }};

                confirmDependencyUpdateBtn.addEventListener('click', confirmHandler, {{ once: true }});
                cancelDependencyUpdateBtn.addEventListener('click', cancelHandler, {{ once: true }});
            }};

            const getDependencyUpdatePlan = (updatedTaskData) => {{
                const tempTasks = tasks.map(t => {{
                    if (t.id === updatedTaskData.id) {{
                        return {{ ...updatedTaskData }};
                    }}
                    return {{ ...t }};
                }});

                const taskMap = new Map(tempTasks.map(t => [t.id, t]));
                const adj = new Map();
                const inDegree = new Map();

                for (const task of tempTasks) {{
                    adj.set(task.id, []);
                    inDegree.set(task.id, 0);
                }}

                for (const task of tempTasks) {{
                    if (task.dependencies) {{
                        const parentIds = task.dependencies.split(',').map(id => parseInt(id.trim()));
                        for (const parentId of parentIds) {{
                            if (adj.has(parentId)) {{
                                adj.get(parentId).push(task.id);
                                inDegree.set(task.id, (inDegree.get(task.id) || 0) + 1);
                            }}
                        }}
                    }}
                }}

                const queue = tempTasks.filter(t => inDegree.get(t.id) === 0).map(t => t.id);
                const sortedOrder = [];
                while (queue.length > 0) {{
                    const u = queue.shift();
                    sortedOrder.push(u);
                    for (const v of (adj.get(u) || [])) {{
                        inDegree.set(v, inDegree.get(v) - 1);
                        if (inDegree.get(v) === 0) {{
                            queue.push(v);
                        }}
                    }}
                }}

                if (sortedOrder.length !== tempTasks.length) {{
                    console.error("Circular dependency detected!");
                    showToast("Error: Circular dependency detected. Cannot update dates.", true);
                    return [];
                }}
                
                const newDates = new Map();
                
                for (const taskId of sortedOrder) {{
                    const task = taskMap.get(taskId);
                    let latestParentEndDate = null;

                    if (task.dependencies) {{
                        const parentIds = task.dependencies.split(',').map(id => parseInt(id.trim()));
                        for (const parentId of parentIds) {{
                            const parent = newDates.get(parentId) || taskMap.get(parentId);
                            if (parent) {{
                                const parentEndDate = parseDate(parent.end);
                                if (!latestParentEndDate || parentEndDate > latestParentEndDate) {{
                                    latestParentEndDate = parentEndDate;
                                }}
                            }}
                        }}
                    }}
                    
                    if (latestParentEndDate) {{
                        const requiredStartDate = addDays(latestParentEndDate, 1);
                        const currentStartDate = parseDate(task.start);
                        if (requiredStartDate > currentStartDate) {{
                            const duration = dayDiff(task.start, task.end);
                            const newStart = requiredStartDate;
                            const newEnd = addDays(newStart, duration);
                            newDates.set(taskId, {{ ...task, start: formatDateToDDMMYYYY(newStart), end: formatDateToDDMMYYYY(newEnd) }});
                        }} else {{
                            newDates.set(taskId, {{ ...task }});
                        }}
                    }} else {{
                         newDates.set(taskId, {{ ...task }});
                    }}
                }}
                
                const updatePlan = [];
                for(const task of tasks) {{
                    const updated = newDates.get(task.id);
                    if (updated && (task.start !== updated.start || task.end !== updated.end)) {{
                        updatePlan.push(updated);
                    }}
                }}
                
                return updatePlan;
            }};

            // --- COLUMN RESIZING LOGIC ---
            const initColumnResizing = () => {{
                document.removeEventListener('mousemove', handleResizeMove);
                document.removeEventListener('mouseup', handleResizeEnd);
                document.querySelectorAll('.resizer').forEach(resizer => {{
                    resizer.addEventListener('mousedown', handleResizeStart);
                }});
            }};

            const handleResizeStart = (e) => {{
                e.preventDefault();
                isResizing = true;
                resizingColumn = e.target.dataset.column;
                dragStartPos = e.clientX;
                document.body.style.cursor = 'col-resize';
                document.addEventListener('mousemove', handleResizeMove);
                document.addEventListener('mouseup', handleResizeEnd);
            }};

            const handleResizeMove = (e) => {{
                if (!isResizing) return;
                const deltaX = e.clientX - dragStartPos;
                const newWidth = columnWidths[resizingColumn] + deltaX;
                if (newWidth > 50) {{
                    document.documentElement.style.setProperty(`--${{resizingColumn}}-width`, `${{newWidth}}px`);
                }}
            }};
            
            const handleResizeEnd = (e) => {{
                if (!isResizing) return;
                isResizing = false;
                const deltaX = e.clientX - dragStartPos;
                const newWidth = columnWidths[resizingColumn] + deltaX;
                if (newWidth > 50) {{
                    columnWidths[resizingColumn] = newWidth;
                }}
                document.documentElement.style.setProperty(`--${{resizingColumn}}-width`, `${{columnWidths[resizingColumn]}}px`);
                document.body.style.cursor = 'default';
                document.removeEventListener('mousemove', handleResizeMove);
                document.removeEventListener('mouseup', handleResizeEnd);
                saveState();
                renderGanttChart();
            }};

            // --- DRAG-AND-DROP LOGIC ---
            const initDragAndDrop = () => {{
                document.removeEventListener('mousemove', handleDragMove);
                document.removeEventListener('mouseup', handleDragEnd);

                ganttChartEl.querySelectorAll('.gantt-bar-wrapper').forEach(barWrapper => {{
                    const taskId = barWrapper.dataset.taskBarId;
                    const taskBar = barWrapper.querySelector('.gantt-bar-bg');
                    if (!barWrapper.querySelector('.gantt-bar-handle.left')) {{
                        const leftHandle = document.createElement('div');
                        leftHandle.className = 'gantt-bar-handle left rounded-l-md';
                        leftHandle.dataset.handleType = 'resize-left';
                        barWrapper.appendChild(leftHandle);
                        const rightHandle = document.createElement('div');
                        rightHandle.className = 'gantt-bar-handle right rounded-r-md';
                        rightHandle.dataset.handleType = 'resize-right';
                        barWrapper.appendChild(rightHandle);
                    }}
                    const handleMouseDown = (e) => {{
                        e.stopPropagation();
                        if (isResizing) return;
                        isDragging = true;
                        currentTaskId = parseInt(taskId);
                        dragStartPos = e.clientX;
                        originalTaskData = {{ ...tasks.find(t => t.id === currentTaskId) }};
                        dragStartStyles = {{ left: barWrapper.offsetLeft, width: barWrapper.offsetWidth }};
                        dragType = e.target.dataset.handleType || 'move'; 
                        document.body.classList.add('select-none');
                        barWrapper.style.zIndex = 30;
                    }};
                    taskBar.addEventListener('mousedown', handleMouseDown);
                    barWrapper.querySelector('.gantt-bar-handle.left').addEventListener('mousedown', handleMouseDown);
                    barWrapper.querySelector('.gantt-bar-handle.right').addEventListener('mousedown', handleMouseDown);
                }});

                document.addEventListener('mousemove', handleDragMove);
                document.addEventListener('mouseup', handleDragEnd);
            }};

            const handleDragMove = (e) => {{
                if (!isDragging) return;
                e.preventDefault();
                const barWrapper = ganttChartEl.querySelector(`.gantt-bar-wrapper[data-task-bar-id="${{currentTaskId}}"]`);
                if (!barWrapper) return;
                const deltaX = e.clientX - dragStartPos;
                if (dragType === 'move') {{
                    barWrapper.style.left = `${{dragStartStyles.left + deltaX}}px`;
                }} else if (dragType === 'resize-right') {{
                    const newWidth = dragStartStyles.width + deltaX;
                    if (newWidth > pixelsPerDay / 2) {{ barWrapper.style.width = `${{newWidth}}px`; }}
                }} else if (dragType === 'resize-left') {{
                    const newWidth = dragStartStyles.width - deltaX;
                    if (newWidth > pixelsPerDay / 2) {{
                        barWrapper.style.left = `${{dragStartStyles.left + deltaX}}px`;
                        barWrapper.style.width = `${{newWidth}}px`;
                    }}
                }}
                drawDependencyArrows();
            }};

            const handleDragEnd = (e) => {{
                if (!isDragging || !currentTaskId) return;
                
                const task = tasks.find(t => t.id === currentTaskId);
                if (!task) {{ isDragging = false; return; }}

                document.body.classList.remove('select-none');
                
                const barWrapper = ganttChartEl.querySelector(`.gantt-bar-wrapper[data-task-bar-id="${{currentTaskId}}"]`);
                if (barWrapper) barWrapper.style.zIndex = 10;
                
                isDragging = false;
                const finalDayShift = Math.round((e.clientX - dragStartPos) / pixelsPerDay);

                if (finalDayShift === 0 && dragType !== 'resize-left' && dragType !== 'resize-right') {{
                    renderGanttChart();
                    return;
                }}
                
                const updatedTaskData = {{ ...task }};
                let newStart, newEnd;
                
                if (dragType === 'move') {{
                    newStart = addDays(parseDate(originalTaskData.start), finalDayShift);
                    newEnd = addDays(newStart, dayDiff(originalTaskData.start, originalTaskData.end));
                }} else if (dragType === 'resize-right') {{
                    newStart = parseDate(task.start);
                    newEnd = addDays(parseDate(originalTaskData.end), finalDayShift);
                    if (newEnd < newStart) newEnd = newStart;
                }} else {{
                    newEnd = parseDate(task.end);
                    newStart = addDays(parseDate(originalTaskData.start), finalDayShift);
                    if (newStart > newEnd) newStart = newEnd;
                }}

                updatedTaskData.start = formatDateToDDMMYYYY(newStart);
                updatedTaskData.end = formatDateToDDMMYYYY(newEnd);

                const updatePlan = getDependencyUpdatePlan(updatedTaskData);

                const performUpdate = () => {{
                    const taskIndex = tasks.findIndex(t => t.id === currentTaskId);
                    if(taskIndex !== -1) tasks[taskIndex] = updatedTaskData;
                    
                    updatePlan.forEach(plannedUpdate => {{
                        const childIndex = tasks.findIndex(t => t.id === plannedUpdate.id);
                        if (childIndex !== -1) {{
                            tasks[childIndex].start = plannedUpdate.start;
                            tasks[childIndex].end = plannedUpdate.end;
                        }}
                    }});
                    renderGanttChart();
                    saveState();
                }};

                if (updatePlan.length > 0) {{
                    const dateShift = dayDiff(originalTaskData.start, updatedTaskData.start);
                    const direction = dateShift > 0 ? 'forward' : 'backward';
                    const modalText = `Shifting this task ${{direction}} by ${{Math.abs(dateShift)}} day(s) will also shift ${{updatePlan.length}} dependent task(s). Do you want to proceed?`;
                    
                    showDependencyModal(updatePlan, modalText, performUpdate, () => renderGanttChart());
                }} else {{
                    performUpdate();
                }}
                currentTaskId = null;
            }};
            
            // --- MODAL & DATA LOGIC ---
            const saveTask = (e) => {{
                e.preventDefault();
                const id = document.getElementById('task-id').value;
                const name = document.getElementById('task-name').value;
                const group = document.getElementById('task-group').value;
                const startValue = document.getElementById('task-start').value;
                const endValue = document.getElementById('task-end').value;
                const progress = parseInt(document.getElementById('task-progress').value, 10);
                const colorInput = document.getElementById('task-color');
                const color = colorInput.disabled ? null : colorInput.value;
                const selectedOptions = Array.from(document.getElementById('task-dependencies').selectedOptions);
                const dependencies = selectedOptions.map(opt => opt.value).join(',');
                
                if (parseDate(startValue) > parseDate(endValue)) {{
                    showToast("End date must be after start date.", true);
                    return;
                }}

                const finalTaskData = {{
                    id: id ? parseInt(id) : null,
                    name, group, 
                    start: formatDateToDDMMYYYY(parseDate(startValue)), 
                    end: formatDateToDDMMYYYY(parseDate(endValue)), 
                    progress, dependencies, color 
                }};
                
                const performUpdate = (isNew = false, updatePlan = []) => {{
                    if (isNew) {{
                        const newId = tasks.length > 0 ? Math.max(...tasks.map(t => t.id)) + 1 : 1;
                        tasks.push({{ ...finalTaskData, id: newId }});
                    }} else {{
                        const taskIndex = tasks.findIndex(t => t.id == id);
                        if (taskIndex !== -1) tasks[taskIndex] = {{ ...tasks[taskIndex], ...finalTaskData }};
                        
                        updatePlan.forEach(plannedUpdate => {{
                            const childIndex = tasks.findIndex(t => t.id === plannedUpdate.id);
                            if (childIndex !== -1) {{
                                tasks[childIndex].start = plannedUpdate.start;
                                tasks[childIndex].end = plannedUpdate.end;
                            }}
                        }});
                    }}
                    renderGanttChart();
                    closeModal();
                    saveState();
                }};

                if (id) {{
                    const updatePlan = getDependencyUpdatePlan(finalTaskData);
                    
                    if (updatePlan.length > 0) {{
                         const modalText = `Updating this task's dates will shift ${{updatePlan.length}} dependent task(s). Do you want to proceed?`;
                         showDependencyModal(updatePlan, modalText, () => performUpdate(false, updatePlan), () => {{}});
                    }} else {{
                        performUpdate(false);
                    }}
                }} else {{
                    performUpdate(true);
                }}
            }};

            const deleteTask = () => {{
                const id = document.getElementById('task-id').value;
                tasks = tasks.filter(t => t.id != id);
                tasks.forEach(task => {{
                    if (task.dependencies) {{
                        const deps = task.dependencies.split(',').map(d => d.trim());
                        task.dependencies = deps.filter(depId => depId != id).join(',');
                    }}
                }});
                renderGanttChart();
                closeModal();
                saveState();
            }};
            
            const openModal = (task = null) => {{
                taskForm.reset();
                delete taskForm.dataset.duration;
                document.getElementById('task-end').min = '';
                const taskId = task ? task.id : null;
                const depsSelect = document.getElementById('task-dependencies');
                depsSelect.innerHTML = '';
                tasks.forEach(t => {{
                    if (t.id !== taskId) {{
                        const option = document.createElement('option');
                        option.value = t.id;
                        option.textContent = `#${{t.id}}: ${{t.name}}`;
                        depsSelect.appendChild(option);
                    }}
                }});
                const groupSelect = document.getElementById('task-group');
                groupSelect.innerHTML = `<option value="">-- No Group --</option>`;
                projectGroups.forEach(group => {{
                    const option = document.createElement('option');
                    option.value = group.name;
                    option.textContent = group.name;
                    groupSelect.appendChild(option);
                }});
                if (task) {{
                    document.getElementById('modal-title').textContent = 'Edit Task';
                    document.getElementById('task-id').value = task.id;
                    document.getElementById('task-name').value = task.name;
                    groupSelect.value = task.group || '';
                    document.getElementById('task-start').value = formatDateToYYYYMMDD(parseDate(task.start));
                    document.getElementById('task-end').value = formatDateToYYYYMMDD(parseDate(task.end));
                    document.getElementById('task-end').min = formatDateToYYYYMMDD(parseDate(task.start));
                    document.getElementById('task-progress').value = task.progress;
                    document.getElementById('progress-value').textContent = task.progress;
                    document.getElementById('delete-task-btn').classList.remove('hidden');
                    taskForm.dataset.duration = dayDiff(task.start, task.end);
                    if (task.dependencies) {{
                        const depIds = task.dependencies.split(',').map(d => d.trim());
                        for (const option of depsSelect.options) {{
                            if (depIds.includes(option.value)) option.selected = true;
                        }}
                    }}
                }} else {{
                    document.getElementById('modal-title').textContent = 'Add New Task';
                    document.getElementById('task-id').value = '';
                    document.getElementById('progress-value').textContent = '0';
                    document.getElementById('delete-task-btn').classList.add('hidden');
                }}
                updateColorPickerState();
                taskModal.classList.remove('hidden');
                taskModal.classList.add('flex');
            }};

            const closeModal = () => {{
                taskModal.classList.add('hidden');
                taskModal.classList.remove('flex');
            }};

            const updateColorPickerState = () => {{
                const groupSelect = document.getElementById('task-group');
                const colorInput = document.getElementById('task-color');
                const selectedGroup = projectGroups.find(g => g.name === groupSelect.value);
                if (selectedGroup) {{
                    colorInput.value = selectedGroup.color;
                    colorInput.disabled = true;
                }} else {{
                    colorInput.disabled = false;
                    const taskId = document.getElementById('task-id').value;
                    const currentTask = tasks.find(t => t.id == taskId);
                    if (currentTask && !currentTask.group && currentTask.color) {{
                        colorInput.value = currentTask.color;
                    }}
                }}
            }};

            const openGroupModal = () => {{
                renderGroupList();
                groupModal.classList.remove('hidden');
                groupModal.classList.add('flex');
            }};

            const closeGroupModal = () => {{
                groupModal.classList.add('hidden');
                groupModal.classList.remove('flex');
            }};

            const renderGroupList = () => {{
                groupListEl.innerHTML = '';
                if (projectGroups.length === 0) {{
                    groupListEl.innerHTML = `<p class="text-sm text-gray-500">No groups defined yet.</p>`;
                    return;
                }}
                projectGroups.forEach(group => {{
                    const groupEl = document.createElement('div');
                    groupEl.className = 'flex items-center justify-between p-2 bg-gray-50 rounded-lg';
                    groupEl.innerHTML = `<div class="flex items-center gap-3"><div class="w-5 h-5 rounded-full" style="background-color: ${{group.color}};"></div><span class="font-medium text-gray-800">${{group.name}}</span></div><button data-group-name="${{group.name}}" class="text-gray-400 hover:text-red-600 delete-group-btn">&times;</button>`;
                    groupListEl.appendChild(groupEl);
                }});
                groupListEl.querySelectorAll('.delete-group-btn').forEach(btn => {{
                    btn.addEventListener('click', () => deleteGroup(btn.dataset.groupName));
                }});
            }};

            const addGroup = (e) => {{
                e.preventDefault();
                const nameInput = document.getElementById('new-group-name');
                const colorInput = document.getElementById('new-group-color');
                const name = nameInput.value.trim();
                if (!name) {{
                    showToast("Group name cannot be empty.", true);
                    return;
                }}
                if (projectGroups.some(g => g.name.toLowerCase() === name.toLowerCase())) {{
                    showToast("A group with this name already exists.", true);
                    return;
                }}
                projectGroups.push({{
                    name,
                    color: colorInput.value
                }});
                addGroupForm.reset();
                colorInput.value = '#79D3C9';
                renderGroupList();
                saveState();
            }};

            const deleteGroup = (groupName) => {{
                projectGroups = projectGroups.filter(g => g.name !== groupName);
                tasks.forEach(task => {{
                    if (task.group === groupName) {{
                        task.group = '';
                    }}
                }});
                renderGroupList();
                renderGanttChart();
                saveState();
            }};

            const downloadAsExcel = () => {{
                const workbook = XLSX.utils.book_new();
                const projectInfoData = [
                    ['Project Title', projectTitleEl.value],
                    ['Project Subtitle', projectSubtitleEl.value]
                ];
                const projectInfoWorksheet = XLSX.utils.aoa_to_sheet(projectInfoData);
                projectInfoWorksheet['!cols'] = [{{ wch: 20 }}, {{ wch: 50 }}];
                XLSX.utils.book_append_sheet(workbook, projectInfoWorksheet, "ProjectInfo");
                if (projectGroups.length > 0) {{
                    const groupsWorksheet = XLSX.utils.json_to_sheet(projectGroups);
                    groupsWorksheet['!cols'] = [{{ wch: 25 }}, {{ wch: 10 }}];
                    XLSX.utils.book_append_sheet(workbook, groupsWorksheet, "Groups");
                }}
                const tasksExportData = tasks.map(({{ id, name, group, start, end, progress, dependencies, color }}) => ({{
                    'Group': group || '',
                    'Task Name': name,
                    'ID': id,
                    'Start Date': start,
                    'End Date': end,
                    'Progress (%)': progress,
                    'Dependencies': dependencies || '',
                    'Color': color || ''
                }}));
                const tasksWorksheet = XLSX.utils.json_to_sheet(tasksExportData);
                tasksWorksheet['!cols'] = [{{ wch: 20 }}, {{ wch: 40 }}, {{ wch: 5 }}, {{ wch: 12 }}, {{ wch: 12 }}, {{ wch: 12 }}, {{ wch: 15 }}, {{ wch: 10 }}];
                XLSX.utils.book_append_sheet(workbook, tasksWorksheet, "Tasks");
                const safeFilename = projectTitleEl.value.replace(/[^a-z0-9]/gi, '_').toLowerCase() || 'gantt_chart';
                XLSX.writeFile(workbook, `${{safeFilename}}.xlsx`);
            }};
            
            const downloadAsHtml = () => {{
                const currentState = {{
                    tasks,
                    projectGroups,
                    viewMode,
                    projectTitle: projectTitleEl.value,
                    projectSubtitle: projectSubtitleEl.value,
                    columnWidths
                }};
                const htmlContent = document.documentElement.outerHTML.replace(
                    'const initialState = {json.dumps(st.session_state.gantt_data)};',
                    `const initialState = ${{JSON.stringify(currentState)}};`
                );
                const blob = new Blob([htmlContent], {{
                    type: 'text/html'
                }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                const safeFilename = projectTitleEl.value.replace(/[^a-z0-9]/gi, '_').toLowerCase() || 'gantt_chart';
                a.download = `${{safeFilename}}.html`;
                a.href = url;
                a.style.display = 'none';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }};

            const handleFileUpload = (event) => {{
                const file = event.target.files[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = (e) => {{
                    try {{
                        const data = new Uint8Array(e.target.result);
                        const workbook = XLSX.read(data, {{
                            type: 'array',
                            cellDates: true
                        }});
                        if (workbook.SheetNames.includes("ProjectInfo")) {{
                            const worksheet = workbook.Sheets["ProjectInfo"];
                            const infoJson = XLSX.utils.sheet_to_json(worksheet, {{
                                header: 1
                            }});
                            const titleRow = infoJson.find(row => row[0] === 'Project Title');
                            const subtitleRow = infoJson.find(row => row[0] === 'Project Subtitle');
                            if (titleRow && titleRow[1]) projectTitleEl.value = titleRow[1];
                            if (subtitleRow && subtitleRow[1]) projectSubtitleEl.value = subtitleRow[1];
                        }}
                        projectGroups = [];
                        if (workbook.SheetNames.includes("Groups")) {{
                            const worksheet = workbook.Sheets["Groups"];
                            projectGroups = XLSX.utils.sheet_to_json(worksheet);
                        }}
                        const tasksSheetName = workbook.SheetNames.includes("Tasks") ? "Tasks" : workbook.SheetNames[0];
                        const worksheet = workbook.Sheets[tasksSheetName];
                        if (!worksheet) throw new Error("No task data sheet found.");
                        const json = XLSX.utils.sheet_to_json(worksheet, {{
                            header: 1
                        }});
                        const headers = json[0].map(h => String(h).trim());
                        const idx = Object.fromEntries(headers.map(h => [h, headers.indexOf(h)]));
                        tasks = json.slice(1).map((row, i) => {{
                            const start = row[idx['Start Date']];
                            const end = row[idx['End Date']];
                            return {{
                                id: row[idx['ID']] ? parseInt(row[idx['ID']]) : i + 1,
                                name: String(row[idx['Task Name']] || ''),
                                group: String(row[idx['Group']] || ''),
                                start: start instanceof Date ? formatDateToDDMMYYYY(start) : String(start || ''),
                                end: end instanceof Date ? formatDateToDDMMYYYY(end) : String(end || ''),
                                progress: parseInt(row[idx['Progress (%)']] || 0),
                                dependencies: String(row[idx['Dependencies']] || ''),
                                color: row[idx['Color']] ? String(row[idx['Color']]) : null
                            }};
                        }}).filter(t => t.name && t.start && t.end);
                        viewModeSelect.value = 'day';
                        renderGanttChart();
                        saveState();
                        showToast('Successfully imported project data!');
                    }} catch (error) {{
                        showToast(error.message, true);
                    }} finally {{
                        event.target.value = '';
                    }}
                }};
                reader.readAsArrayBuffer(file);
            }};

            // --- MAIN RENDER FUNCTION ---
            const renderGanttChart = () => {{
                if (!ganttChartEl) return;
                const scrollLeft = ganttChartContainerEl.scrollLeft;
                const scrollTop = ganttChartContainerEl.scrollTop;
                ganttChartEl.innerHTML = ''; 
                dependencyLinesEl.innerHTML = '';
                document.documentElement.style.setProperty('--group-width', `${{columnWidths.group}}px`);
                document.documentElement.style.setProperty('--task-name-width', `${{columnWidths.taskName}}px`);
                document.documentElement.style.setProperty('--deps-width', `${{columnWidths.deps}}px`);
                if (tasks.length === 0) {{
                    ganttChartEl.innerHTML = `<div class="text-center p-10 text-gray-500 col-span-full">No tasks yet. Click '+ Add Task' to begin.</div>`;
                    return;
                }}
                const groupColors = Object.fromEntries(projectGroups.map(g => [g.name, g.color]));
                tasks.sort((a, b) => (a.group || 'zzzz').localeCompare(b.group || 'zzzz') || parseDate(a.start) - parseDate(b.start));
                const allDates = tasks.flatMap(t => [parseDate(t.start), parseDate(t.end)]).filter(d => d && !isNaN(d));
                if (allDates.length === 0) {{
                    ganttChartEl.innerHTML = `<div class="text-center p-10 text-gray-500 col-span-full">No valid dates found in tasks.</div>`;
                    return;
                }};
                chartStartDate = addDays(new Date(Math.min(...allDates)), -2);
                let chartEndDate = addDays(new Date(Math.max(...allDates)), 2);
                let headers = [];
                const columnWidth = viewMode === 'day' ? 40 : viewMode === 'week' ? 60 : viewMode === 'month' ? 80 : 120;
                if (viewMode === 'day') {{
                    let d = new Date(chartStartDate);
                    while (d <= chartEndDate) {{
                        headers.push({{
                            label: d.getUTCDate(),
                            subLabel: d.getUTCDate() === 1 || headers.length === 0 ? d.toLocaleString('default', {{ month: 'short', timeZone: 'UTC' }}) : '',
                            isWeekend: [0, 6].includes(d.getUTCDay()),
                            startDate: new Date(d),
                            days: 1
                        }});
                        d = addDays(d, 1);
                    }}
                }} else {{
                     let unitStartDate = new Date(chartStartDate);
                    while (unitStartDate <= chartEndDate) {{
                        let unitEndDate, label, subLabel;
                        const year = unitStartDate.getUTCFullYear();
                        if (viewMode === 'week') {{
                            const dayOfWeek = unitStartDate.getUTCDay();
                            const startOfWeek = addDays(unitStartDate, -dayOfWeek);
                            unitEndDate = addDays(startOfWeek, 6);
                            const weekNum = Math.ceil(( (startOfWeek - new Date(Date.UTC(year, 0, 1))) / 86400000 + 1) / 7);
                            label = `W${{weekNum}}`;
                            subLabel = `${{startOfWeek.getUTCDate()}}/${{startOfWeek.getUTCMonth() + 1}}`;

                        }} else if (viewMode === 'month') {{
                            unitStartDate = new Date(Date.UTC(year, unitStartDate.getUTCMonth(), 1));
                            unitEndDate = new Date(Date.UTC(year, unitStartDate.getUTCMonth() + 1, 0));
                            label = unitStartDate.toLocaleString('default', {{ month: 'short', year: 'numeric', timeZone: 'UTC' }});
                        }} else if (viewMode === 'quarter') {{
                            const q = Math.floor(unitStartDate.getUTCMonth() / 3);
                            unitStartDate = new Date(Date.UTC(year, q * 3, 1));
                            unitEndDate = new Date(Date.UTC(year, unitStartDate.getUTCMonth() + 3, 0));
                            label = `Q${{q + 1}} ${{year}}`;
                        }} else if (viewMode === 'year') {{
                            unitStartDate = new Date(Date.UTC(year, 0, 1));
                            unitEndDate = new Date(Date.UTC(year, 11, 31));
                            label = year;
                        }}
                        headers.push({{
                            label, subLabel,
                            startDate: new Date(unitStartDate),
                            days: dayDiff(formatDateToYYYYMMDD(unitStartDate), formatDateToYYYYMMDD(unitEndDate)) + 1
                        }});
                        unitStartDate = addDays(unitEndDate, 1);
                    }}
                    chartStartDate = headers[0].startDate;
                }}
                const finalChartEndDate = addDays(headers[headers.length - 1].startDate, headers[headers.length - 1].days);
                const totalChartDays = dayDiff(formatDateToYYYYMMDD(chartStartDate), formatDateToYYYYMMDD(finalChartEndDate));
                const frozenWidth = columnWidths.group + columnWidths.taskName + columnWidths.deps;
                const timelineContainerWidth = ganttChartContainerEl.offsetWidth - frozenWidth;
                const totalTimelinePixelWidth = Math.max(timelineContainerWidth, headers.length * columnWidth);
                pixelsPerDay = totalTimelinePixelWidth / totalChartDays;
                ganttChartEl.style.gridTemplateColumns = `var(--group-width) var(--task-name-width) var(--deps-width) repeat(${{headers.length}}, 1fr)`;
                ganttChartEl.style.width = `${{frozenWidth + totalTimelinePixelWidth}}px`;
                const createHeaderCell = (content, col, stickyLeft, hasResizer = false) => {{
                    const cell = document.createElement('div');
                    cell.className = 'sticky top-0 z-20 bg-gray-100 p-3 font-semibold text-sm border-b border-r border-gray-200 flex items-center justify-between relative';
                    cell.style.gridColumn = col;
                    cell.innerHTML = content;
                    if (stickyLeft !== null) cell.style.left = stickyLeft;
                    if (hasResizer) cell.innerHTML += `<div class="resizer" data-column="${{hasResizer}}"></div>`;
                    return cell;
                }}
                const groupHeader = createHeaderCell('Group', '1', '0px', 'group');
                groupHeader.classList.add('z-30');
                ganttChartEl.appendChild(groupHeader);
                ganttChartEl.appendChild(createHeaderCell('Task Name', '2', 'var(--group-width)', 'taskName'));
                ganttChartEl.appendChild(createHeaderCell('Depends On', '3', 'calc(var(--group-width) + var(--task-name-width))'));
                headers.forEach((h, i) => {{
                    const cell = document.createElement('div');
                    cell.className = `sticky top-0 z-10 text-center border-b border-l border-gray-200 text-xs text-gray-500 ${{h.isWeekend ? 'bg-gray-200/50' : 'bg-gray-100/50'}}`;
                    cell.style.cssText = `grid-column: ${{i+4}}; height:${{taskRowHeight}}px; display:flex; flex-direction:column; justify-content:center;`;
                    cell.innerHTML = `${{h.subLabel ? `<div class="text-gray-700 font-medium">${{h.subLabel}}</div>` : ''}}<div>${{h.label}}</div>`;
                    ganttChartEl.appendChild(cell);
                }});
                tasks.forEach((task, taskIndex) => {{
                    const createDataCell = (content, col, stickyLeft) => {{
                        const cell = document.createElement('div');
                        cell.className = 'sticky z-10 bg-white p-3 border-b border-r border-gray-200 text-sm truncate';
                        cell.style.cssText = `grid-row: ${{taskIndex+2}}; grid-column: ${{col}}; left: ${{stickyLeft}};`;
                        cell.textContent = content;
                        return cell;
                    }}
                    ganttChartEl.appendChild(createDataCell(task.group || '', '1', '0px'));
                    
                    const taskNameCell = createDataCell(task.name, '2', 'var(--group-width)');
                    taskNameCell.classList.add('hover:bg-gray-50', 'cursor-pointer');
                    taskNameCell.title = `Click to edit task: "${{task.name}}"`;
                    taskNameCell.addEventListener('click', () => openModal(task));
                    ganttChartEl.appendChild(taskNameCell);

                    ganttChartEl.appendChild(createDataCell(task.dependencies || '', '3', 'calc(var(--group-width) + var(--task-name-width))'));
                    const timelineCell = document.createElement('div');
                    timelineCell.className = 'relative border-b border-gray-200 task-row-timeline';
                    timelineCell.style.cssText = `grid-row: ${{taskIndex+2}}; grid-column: 4 / -1;`;
                    const startPos = dayDiff(formatDateToYYYYMMDD(chartStartDate), task.start) * pixelsPerDay;
                    const barDurationDays = dayDiff(task.start, task.end);
                    const barWidth = (barDurationDays + 1) * pixelsPerDay;
                    const barColor = task.color || groupColors[task.group] || '#79D3C9';
                    timelineCell.innerHTML = `<div class="gantt-bar-wrapper" data-task-bar-id="${{task.id}}" style="position: absolute; left: ${{startPos}}px; width: ${{barWidth}}px; top:0; height: 100%"><div class="absolute top-1/2 -translate-y-1/2 left-0 w-full h-3/5 rounded-md gantt-bar-bg shadow-sm" style="background-color: ${{barColor}}40;"><div class="h-full rounded-md gantt-bar-progress" style="width: ${{task.progress}}%; background-color: ${{barColor}};"></div></div><div class="gantt-tooltip absolute bottom-full mb-2 w-max max-w-xs p-3 rounded-lg shadow-lg text-sm z-30" style="background-color: #006152; color: white;"><div class="font-bold">#${{task.id}}: ${{task.name}}</div><div>${{task.start}} to ${{task.end}}</div><div>Duration: ${{barDurationDays + 1}} days</div><div>Progress: <span class="font-semibold">${{task.progress}}%</span></div></div></div>`;
                    
                    timelineCell.addEventListener('click', (e) => {{
                        if (!e.target.closest('.gantt-bar-wrapper')) {{
                            openModal(task);
                        }}
                    }});
                    
                    ganttChartEl.appendChild(timelineCell);

                    timelineCell.querySelector('.gantt-bar-wrapper')?.addEventListener('contextmenu', (e) => {{
                        e.preventDefault();
                        openModal(task);
                    }});
                }});
                initDragAndDrop();
                initColumnResizing();
                ganttChartContainerEl.scrollLeft = scrollLeft;
                ganttChartContainerEl.scrollTop = scrollTop;
                setTimeout(() => drawDependencyArrows(), 50);
            }};

            const drawDependencyArrows = () => {{
                if (tasks.length === 0) return;
                dependencyLinesEl.innerHTML = `<defs><marker id="arrow-head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#006152" opacity="0.8"></path></marker><marker id="arrow-head-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#DC2626" opacity="0.8"></path></marker></defs>`;
                dependencyLinesEl.style.width = `${{ganttChartEl.scrollWidth}}px`;
                dependencyLinesEl.style.height = `${{ganttChartEl.scrollHeight}}px`;
                
                tasks.forEach(task => {{
                    if (!task.dependencies) return;
                    const childBarWrapper = ganttChartEl.querySelector(`.gantt-bar-wrapper[data-task-bar-id="${{task.id}}"]`);
                    if (!childBarWrapper) return;
                    const childTimelineCell = childBarWrapper.closest('.task-row-timeline');
                    if (!childTimelineCell) return;
                    const childRowTop = childTimelineCell.offsetTop;
                    const endY = childRowTop + (childTimelineCell.offsetHeight / 2);
                    const endX = childTimelineCell.offsetLeft + childBarWrapper.offsetLeft;
                    task.dependencies.split(',').forEach(depId => {{
                        const parentBarWrapper = ganttChartEl.querySelector(`.gantt-bar-wrapper[data-task-bar-id="${{depId.trim()}}"]`);
                        if (!parentBarWrapper) return;
                        const parentTimelineCell = parentBarWrapper.closest('.task-row-timeline');
                        if (!parentTimelineCell) return;
                        const parentRowTop = parentTimelineCell.offsetTop;
                        const startY = parentRowTop + (parentTimelineCell.offsetHeight / 2);
                        const startX = parentTimelineCell.offsetLeft + parentBarWrapper.offsetLeft + parentBarWrapper.offsetWidth;
                        const neck = 15;
                        const pathD = `M ${{startX}} ${{startY}} H ${{startX + neck}} V ${{endY}} H ${{endX}}`;
                        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                        path.setAttribute('d', pathD);
                        const isConflict = endX < startX;
                        path.setAttribute('stroke', isConflict ? '#DC2626' : '#006152');
                        path.setAttribute('marker-end', isConflict ? 'url(#arrow-head-red)' : 'url(#arrow-head)');
                        path.setAttribute('fill', 'none');
                        path.setAttribute('stroke-width', '1.5');
                        path.setAttribute('opacity', '0.8');
                        dependencyLinesEl.appendChild(path);
                    }});
                }});
            }};

            // --- INITIALIZATION & EVENT LISTENERS ---
            const handleStartDateChange = (e) => {{
                const taskEndInput = document.getElementById('task-end');
                const startDate = e.target.value;
                if (startDate) {{
                    taskEndInput.min = startDate;
                    if (taskForm.dataset.duration) {{
                        const duration = parseInt(taskForm.dataset.duration, 10);
                        const newEndDate = addDays(parseDate(startDate), duration);
                        taskEndInput.value = formatDateToYYYYMMDD(newEndDate);
                    }} else if (!taskEndInput.value || parseDate(taskEndInput.value) < parseDate(startDate)) {{
                        taskEndInput.value = startDate;
                    }}
                }}
            }};

            document.getElementById('task-start').addEventListener('input', handleStartDateChange);
            document.getElementById('task-end').addEventListener('input', () => {{ delete taskForm.dataset.duration; }});
            document.getElementById('task-group').addEventListener('change', updateColorPickerState);
            document.getElementById('task-progress').addEventListener('input', (e) => {{ document.getElementById('progress-value').textContent = e.target.value; }});
            currentDateEl.textContent = new Intl.DateTimeFormat('en-GB', {{ day: '2-digit', month: '2-digit', year: 'numeric' }}).format(new Date());
            addTaskBtn.addEventListener('click', () => openModal());
            cancelBtn.addEventListener('click', closeModal);
            taskForm.addEventListener('submit', saveTask);
            deleteTaskBtn.addEventListener('click', deleteTask);
            downloadBtn.addEventListener('click', downloadAsExcel);
            downloadHtmlBtn.addEventListener('click', downloadAsHtml);
            clearDataBtn.addEventListener('click', clearState);
            printBtn.addEventListener('click', () => window.print());
            fileInput.addEventListener('change', handleFileUpload);
            viewModeSelect.addEventListener('change', (e) => {{ viewMode = e.target.value; saveState(); renderGanttChart(); }});
            manageGroupsBtn.addEventListener('click', openGroupModal);
            closeGroupModalBtn.addEventListener('click', closeGroupModal);
            addGroupForm.addEventListener('submit', addGroup);
            projectTitleEl.addEventListener('change', saveState);
            projectSubtitleEl.addEventListener('change', saveState);
            window.addEventListener('resize', renderGanttChart);
            ganttChartContainerEl.addEventListener('scroll', drawDependencyArrows);
            
            // Initialize the chart
            renderGanttChart();
        }});
    </script>
</body>
</html>
"""

# Sidebar controls
with st.sidebar:
    st.header("🎯 Gantt Chart Controls")
    
    if st.button("🆕 Add Sample Data"):
        sample_data = {
            'tasks': [
                {
                    'id': 1,
                    'name': 'Project Planning',
                    'group': 'Planning',
                    'start': '01/01/2024',
                    'end': '15/01/2024',
                    'progress': 100,
                    'dependencies': '',
                    'color': '#79D3C9'
                },
                {
                    'id': 2,
                    'name': 'Design Phase',
                    'group': 'Design',
                    'start': '16/01/2024',
                    'end': '31/01/2024',
                    'progress': 75,
                    'dependencies': '1',
                    'color': '#25B8A3'
                },
                {
                    'id': 3,
                    'name': 'Development',
                    'group': 'Development',
                    'start': '01/02/2024',
                    'end': '29/02/2024',
                    'progress': 50,
                    'dependencies': '2',
                    'color': '#006152'
                },
                {
                    'id': 4,
                    'name': 'Testing',
                    'group': 'Testing',
                    'start': '01/03/2024',
                    'end': '15/03/2024',
                    'progress': 25,
                    'dependencies': '3',
                    'color': '#FF6B6B'
                },
                {
                    'id': 5,
                    'name': 'Deployment',
                    'group': 'Deployment',
                    'start': '16/03/2024',
                    'end': '31/03/2024',
                    'progress': 0,
                    'dependencies': '4',
                    'color': '#4ECDC4'
                }
            ],
            'projectGroups': [
                {'name': 'Planning', 'color': '#79D3C9'},
                {'name': 'Design', 'color': '#25B8A3'},
                {'name': 'Development', 'color': '#006152'},
                {'name': 'Testing', 'color': '#FF6B6B'},
                {'name': 'Deployment', 'color': '#4ECDC4'}
            ],
            'projectTitle': 'Software Development Project',
            'projectSubtitle': 'Q1 2024 Timeline'
        }
        st.session_state.gantt_data = sample_data
        st.rerun()
    
    if st.button("🗑️ Clear All Data"):
        st.session_state.gantt_data = {
            'tasks': [],
            'projectGroups': [],
            'projectTitle': 'Project Timeline',
            'projectSubtitle': 'Interactive Gantt Chart'
        }
        st.rerun()
    
    st.markdown("---")
    st.header("📊 Current Stats")
    st.write(f"Tasks: {len(st.session_state.gantt_data['tasks'])}")
    st.write(f"Groups: {len(st.session_state.gantt_data['projectGroups'])}")
    
    st.markdown("---")
    st.header("ℹ️ Instructions")
    st.markdown("""
    - **Click + Add Task** to create new tasks
    - **Drag tasks** to adjust dates
    - **Resize tasks** by dragging edges
    - **Click task names** to edit
    - **Right-click bars** for quick edit
    - **Manage groups** for color coding
    - **Export/Import** Excel files
    """)

# Handle messages from the component
def handle_component_message(message):
    if message and hasattr(message, 'get'):
        if message.get('type') == 'GANTT_CHART_UPDATE':
            st.session_state.gantt_data = message['data']
            st.success("✅ Gantt chart updated!")

# Render the Gantt chart component
result = components.html(
    gantt_chart_html,
    height=800,
    scrolling=True
)

# Process messages from the component
if result is not None:
    handle_component_message(result)

# Display current data in expandable section
with st.expander("📁 View Current Project Data"):
    st.json(st.session_state.gantt_data)

# Footer
st.markdown("---")
st.markdown(
    "**Gantt Chart Project Manager** | Built with Streamlit • "
    "Drag and drop to manage your project timeline efficiently"
)

# import streamlit as st
# import streamlit.components.v1 as components

# # Set the Streamlit page configuration to use the "wide" layout.
# # This gives your Gantt chart more horizontal space.
# st.set_page_config(layout="wide")

# # --- HTML, CSS, and JavaScript for the Gantt Chart ---
# # The entire code for your Gantt chart application is contained in this multiline string.
# gantt_chart_html = """
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Gantt Chart</title>
#     <script src="https://cdn.tailwindcss.com"></script>
#     <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
#     <link rel="preconnect" href="https://fonts.googleapis.com">
#     <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
#     <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
#     <style>
#         :root {
#             --group-width: 150px;
#             --task-name-width: 250px;
#             --deps-width: 100px;
#         }
#         body {
#             font-family: 'Inter', sans-serif;
#             overflow: hidden; /* Prevent body scroll, all scrolling is in the container */
#         }
#         /* Adjust the container height for Streamlit's iframe environment */
#         .main-container {
#             height: 95vh; 
#             display: flex;
#             flex-direction: column;
#         }
#         .gantt-chart-container {
#             flex-grow: 1;
#             overflow: auto; /* The main scrollable area */
#         }
#         #gantt-chart {
#             display: inline-grid;
#         }
#         .gantt-chart-container::-webkit-scrollbar {
#             width: 8px;
#             height: 8px;
#         }
#         .gantt-chart-container::-webkit-scrollbar-track {
#             background: #f1f1f1;
#             border-radius: 10px;
#         }
#         .gantt-chart-container::-webkit-scrollbar-thumb {
#             background: #ccc;
#             border-radius: 10px;
#         }
#         .gantt-chart-container::-webkit-scrollbar-thumb:hover {
#             background: #aaa;
#         }
#         .gantt-tooltip {
#             visibility: hidden;
#             opacity: 0;
#             transition: opacity 0.3s;
#         }
#         .gantt-bar-wrapper:hover .gantt-tooltip {
#             visibility: visible;
#             opacity: 1;
#         }
#         input[type="range"]::-webkit-slider-thumb {
#             -webkit-appearance: none;
#             appearance: none;
#             width: 20px;
#             height: 20px;
#             background: #006152;
#             cursor: pointer;
#             border-radius: 50%;
#         }
#         input[type="range"]::-moz-range-thumb {
#             width: 20px;
#             height: 20px;
#             background: #006152;
#             cursor: pointer;
#             border-radius: 50%;
#         }

#         #dependency-lines {
#             position: absolute;
#             top: 0;
#             left: 0;
#             pointer-events: none;
#             overflow: visible;
#             z-index: 5;
#         }

#         /* Drag Handles */
#         .gantt-bar-handle {
#             position: absolute;
#             top: 0;
#             height: 100%;
#             width: 8px;
#             cursor: ew-resize;
#             z-index: 10;
#         }
#         .gantt-bar-handle.left { left: -4px; }
#         .gantt-bar-handle.right { right: -4px; }
#         .gantt-bar-bg { cursor: grab; }
#         .gantt-bar-bg:active { cursor: grabbing; }

#         /* Column Resizer */
#         .resizer {
#             position: absolute;
#             top: 0;
#             right: 0;
#             width: 5px;
#             height: 100%;
#             cursor: col-resize;
#             user-select: none;
#             z-index: 40;
#         }

#         /* --- PRINT STYLES --- */
#         @media print {
#             @page {
#                 size: A3 landscape;
#                 margin: 1cm;
#             }
#             * {
#                 -webkit-print-color-adjust: exact !important;
#                 print-color-adjust: exact !important;
#                 box-shadow: none !important;
#             }
#             body { padding: 0 !important; margin: 0 !important; background-color: #fff !important; overflow: visible; }
#             .main-container { height: auto; }
#             header > div:last-child, footer, #task-modal, #group-modal, .gantt-tooltip, .gantt-bar-handle, .resizer, #dependency-modal {
#                 display: none !important;
#             }
#             .max-w-7xl { margin: 0 !important; max-width: 100% !important; border: none !important; overflow: visible !important; }
#             header { border-bottom: 2px solid #ccc !important; justify-content: flex-start !important; }
#             #project-title, #project-subtitle { color: #000 !important; }
#             .gantt-chart-container {
#                 overflow: visible !important;
#                 padding: 0 !important;
#                 border: 1px solid #eee;
#             }
#             .sticky { position: static !important; }
#             #dependency-lines { display: block !important; position: absolute !important; }
#         }
#     </style>
# </head>
# <body class="bg-gray-100 p-4 sm:p-6 lg:p-8">

#     <div class="max-w-7xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden main-container">
#         <header class="p-5 text-white flex justify-between items-center flex-wrap gap-4" style="background-color: #006152;">
#             <div>
#                 <input type="text" id="project-title" value="Project Timeline" class="text-2xl font-bold bg-transparent border-none text-white w-full focus:outline-none focus:ring-1 focus:ring-white/50 rounded-md p-1 -m-1">
#                 <input type="text" id="project-subtitle" value="Interactive Gantt Chart" class="text-sm opacity-90 bg-transparent border-none text-white w-full focus:outline-none focus:ring-1 focus:ring-white/50 rounded-md p-1 -m-1 mt-1">
#             </div>
#             <div class="flex items-center gap-2 flex-wrap">
#                  <button id="manage-groups-btn" class="px-3 py-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors text-sm focus:outline-none focus:ring-2 focus:ring-white">Manage Groups</button>
#                 <select id="view-mode" class="bg-white/20 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-white">
#                     <option value="day" class="text-black">Days</option>
#                     <option value="week" class="text-black">Weeks</option>
#                     <option value="month" class="text-black">Months</option>
#                     <option value="quarter" class="text-black">Quarters</option>
#                     <option value="year" class="text-black">Years</option>
#                 </select>
#                 <label for="file-input" class="cursor-pointer p-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors focus:outline-none focus:ring-2 focus:ring-white" title="Upload Excel">
#                     <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd" /></svg>
#                 </label>
#                 <input type="file" id="file-input" class="hidden" accept=".xlsx, .xls">
#                 <button id="download-btn" title="Download Excel" class="p-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors focus:outline-none focus:ring-2 focus:ring-white">
#                     <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
#                 </button>
#                  <button id="clear-data-btn" title="Clear All Local Data" class="p-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors focus:outline-none focus:ring-2 focus:ring-white">
#                     <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
#                         <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm4 0a1 1 0 012 0v6a1 1 0 11-2 0V8z" clip-rule="evenodd" />
#                     </svg>
#                 </button>
#                 <button id="download-html-btn" title="Download as HTML" class="p-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors focus:outline-none focus:ring-2 focus:ring-white">
#                     <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
#                         <path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clip-rule="evenodd" />
#                     </svg>
#                 </button>
#                  <button id="print-btn" title="Print to PDF" class="p-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors focus:outline-none focus:ring-2 focus:ring-white">
#                     <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5 4v3H4a2 2 0 00-2 2v6a2 2 0 002 2h12a2 2 0 002-2V9a2 2 0 00-2-2h-1V4a2 2 0 00-2-2H7a2 2 0 00-2 2zm8 0H7v3h6V4zm0 8H7v4h6v-4z" clip-rule="evenodd" /></svg>
#                 </button>
#                 <button id="add-task-btn" class="px-4 py-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors focus:outline-none focus:ring-2 focus:ring-white">
#                     + Add Task
#                 </button>
#             </div>
#         </header>

#         <div id="gantt-chart-container" class="gantt-chart-container relative">
#             <div id="gantt-chart" class="relative"></div>
#             <svg id="dependency-lines"></svg>
#         </div>
#          <footer class="p-4 bg-gray-50 border-t border-gray-200 text-xs text-gray-500 text-center">
#             <p>Generated on: <span id="current-date"></span></p>
#             <p class="mt-1">Created by Dave Maher</p>
#         </footer>
#     </div>
    
#     <!-- Modals -->
#     <div id="group-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50 p-4">
#         <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
#             <h2 class="text-xl font-bold text-gray-800 mb-4">Manage Groups</h2>
#             <div id="group-list" class="mb-4 max-h-60 overflow-y-auto pr-2 space-y-2"></div>
#             <form id="add-group-form" class="mt-4 border-t pt-4">
#                 <p class="text-sm font-medium text-gray-700 mb-2">Add New Group</p>
#                 <div class="flex items-center gap-3">
#                     <input type="text" id="new-group-name" placeholder="Group Name" class="flex-grow p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500" required>
#                     <input type="color" id="new-group-color" value="#79D3C9" class="w-10 h-10 p-1 border border-gray-300 rounded-lg">
#                     <button type="submit" class="px-4 py-2 text-white rounded-lg" style="background-color: #006152;">Add</button>
#                 </div>
#             </form>
#             <div class="flex justify-end mt-6">
#                 <button type="button" id="close-group-modal-btn" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300">Done</button>
#             </div>
#         </div>
#     </div>
#     <div id="task-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50 p-4">
#         <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
#             <h2 id="modal-title" class="text-xl font-bold text-gray-800 mb-6">Add New Task</h2>
#             <form id="task-form">
#                 <input type="hidden" id="task-id">
#                 <div class="grid grid-cols-2 gap-4 mb-4">
#                     <div>
#                          <label for="task-group" class="block text-sm font-medium text-gray-700 mb-1">Group</label>
#                          <select id="task-group" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"></select>
#                     </div>
#                     <div>
#                         <label for="task-name" class="block text-sm font-medium text-gray-700 mb-1">Task Name</label>
#                         <input type="text" id="task-name" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500" required>
#                     </div>
#                 </div>
#                 <div class="mb-4">
#                     <label for="task-dependencies" class="block text-sm font-medium text-gray-700 mb-1">Dependencies</label>
#                     <select id="task-dependencies" multiple class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 h-24"></select>
#                 </div>
#                 <div class="grid grid-cols-2 gap-4 mb-4">
#                     <div>
#                         <label for="task-start" class="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
#                         <input type="date" id="task-start" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500" required>
#                     </div>
#                     <div>
#                         <label for="task-end" class="block text-sm font-medium text-gray-700 mb-1">End Date</label>
#                         <input type="date" id="task-end" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500" required>
#                     </div>
#                 </div>
#                 <div class="flex items-center gap-4 mb-6">
#                     <div class="flex-grow">
#                         <label for="task-progress" class="block text-sm font-medium text-gray-700 mb-1">Progress (<span id="progress-value">0</span>%)</label>
#                         <input type="range" id="task-progress" min="0" max="100" value="0" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
#                     </div>
#                     <div>
#                          <label for="task-color" class="block text-sm font-medium text-gray-700 mb-1">Color</label>
#                         <input type="color" id="task-color" value="#25B8A3" class="w-10 h-10 p-1 border border-gray-300 rounded-lg disabled:opacity-50">
#                     </div>
#                 </div>
#                 <div class="flex justify-end gap-3">
#                     <button type="button" id="delete-task-btn" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50 hidden mr-auto">Delete</button>
#                     <button type="button" id="cancel-btn" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-opacity-50">Cancel</button>
#                     <button type="submit" id="save-task-btn" class="px-4 py-2 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-opacity-50" style="background-color: #006152; hover:background-color: #004c40;">Save Task</button>
#                 </div>
#             </form>
#         </div>
#     </div>

#     <!-- Dependency Confirmation Modal -->
#     <div id="dependency-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50 p-4">
#         <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
#             <h2 class="text-xl font-bold text-gray-800 mb-4">Update Dependent Tasks?</h2>
#             <p id="dependency-modal-text" class="text-sm text-gray-600 mb-4">Changing this task's dates will affect the following dependent tasks. Do you want to automatically shift their dates?</p>
#             <div id="dependent-tasks-list" class="mb-4 max-h-40 overflow-y-auto pr-2 space-y-2 text-sm">
#                 <!-- Dependent tasks will be listed here -->
#             </div>
#             <div class="flex justify-end gap-3 mt-6">
#                 <button type="button" id="cancel-dependency-update" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300">Cancel</button>
#                 <button type="button" id="confirm-dependency-update" class="px-4 py-2 text-white rounded-lg" style="background-color: #006152;">Yes, Update</button>
#             </div>
#         </div>
#     </div>


#     <script>
#         document.addEventListener('DOMContentLoaded', () => {
#             // --- STATE & CONFIGURATION ---
#             let viewMode = 'day'; 
#             let tasks = []; 
#             let projectGroups = [];
#             let columnWidths = {
#                 group: 150,
#                 taskName: 250,
#                 deps: 100
#             };

#             // Chart dimensions
#             let chartStartDate = null;
#             let pixelsPerDay = 0;
#             let taskRowHeight = 40;

#             // Drag states
#             let isDragging = false;
#             let currentTaskId = null;
#             let dragStartPos = 0;
#             let dragType = 'move';
#             let originalTaskData = null;
#             let dragStartStyles = null;
#             let isResizing = false;
#             let resizingColumn = null;

#             // --- DOM ELEMENTS ---
#             const ganttChartContainerEl = document.getElementById('gantt-chart-container');
#             const ganttChartEl = document.getElementById('gantt-chart');
#             const dependencyLinesEl = document.getElementById('dependency-lines');
#             const currentDateEl = document.getElementById('current-date');
#             const addTaskBtn = document.getElementById('add-task-btn');
#             const taskModal = document.getElementById('task-modal');
#             const taskForm = document.getElementById('task-form');
#             const cancelBtn = document.getElementById('cancel-btn');
#             const deleteTaskBtn = document.getElementById('delete-task-btn');
#             const downloadBtn = document.getElementById('download-btn');
#             const downloadHtmlBtn = document.getElementById('download-html-btn');
#             const clearDataBtn = document.getElementById('clear-data-btn');
#             const printBtn = document.getElementById('print-btn');
#             const fileInput = document.getElementById('file-input');
#             const projectTitleEl = document.getElementById('project-title');
#             const projectSubtitleEl = document.getElementById('project-subtitle');
#             const viewModeSelect = document.getElementById('view-mode');
#             const manageGroupsBtn = document.getElementById('manage-groups-btn');
#             const groupModal = document.getElementById('group-modal');
#             const closeGroupModalBtn = document.getElementById('close-group-modal-btn');
#             const addGroupForm = document.getElementById('add-group-form');
#             const groupListEl = document.getElementById('group-list');
#             const dependencyModal = document.getElementById('dependency-modal');
#             const dependencyModalText = document.getElementById('dependency-modal-text');
#             const dependentTasksListEl = document.getElementById('dependent-tasks-list');
#             const confirmDependencyUpdateBtn = document.getElementById('confirm-dependency-update');
#             const cancelDependencyUpdateBtn = document.getElementById('cancel-dependency-update');

#             // --- UTILITY FUNCTIONS ---
#             const formatDateToDDMMYYYY = (date) => {
#                 if (!date || isNaN(date.getTime())) return '';
#                 const day = String(date.getUTCDate()).padStart(2, '0');
#                 const month = String(date.getUTCMonth() + 1).padStart(2, '0');
#                 const year = date.getUTCFullYear();
#                 return `${day}/${month}/${year}`;
#             };

#             const formatDateToYYYYMMDD = (date) => {
#                 if (!date || isNaN(date.getTime())) return '';
#                 return date.toISOString().slice(0, 10);
#             };

#             const parseDate = (dateStr) => {
#                 if (!dateStr) return null;
#                 if (dateStr instanceof Date) { // Handle date objects directly
#                     return new Date(Date.UTC(dateStr.getFullYear(), dateStr.getMonth(), dateStr.getDate()));
#                 }
#                 if (typeof dateStr !== 'string') return null;

#                 // Try parsing dd/mm/yyyy
#                 const partsDMY = dateStr.split('/');
#                 if (partsDMY.length === 3) {
#                     const [day, month, year] = partsDMY.map(Number);
#                     if (year > 1000 && month >= 1 && month <= 12 && day >= 1 && day <= 31) {
#                         return new Date(Date.UTC(year, month - 1, day));
#                     }
#                 }
#                 // Try parsing yyyy-mm-dd
#                 const partsYMD = dateStr.split('-');
#                 if (partsYMD.length === 3) {
#                     const [year, month, day] = partsYMD.map(Number);
#                     if (year > 1000 && month >= 1 && month <= 12 && day >= 1 && day <= 31) {
#                         return new Date(Date.UTC(year, month - 1, day));
#                     }
#                 }
#                 return null;
#             };

#             const addDays = (date, days) => {
#                 const result = new Date(date);
#                 result.setUTCDate(result.getUTCDate() + days);
#                 return result;
#             };

#             const dayDiff = (startDateStr, endDateStr) => {
#                 const msPerDay = 1000 * 60 * 60 * 24;
#                 const start = parseDate(startDateStr);
#                 const end = parseDate(endDateStr);
#                 if (!start || !end) return 0;
#                 // Add a small epsilon to handle floating point issues with timezones
#                 return Math.round((end - start) / msPerDay + 0.00001);
#             };

#             const showToast = (message, isError = false, needsConfirmation = false) => {
#                 const toastId = 'gantt-toast';
#                 document.getElementById(toastId)?.remove();
#                 const toast = document.createElement('div');
#                 toast.id = toastId;
#                 toast.className = `fixed bottom-5 right-5 p-4 rounded-lg shadow-lg text-white z-50 transform translate-y-20 opacity-0 transition-all duration-300`;
#                 toast.textContent = message;
#                 let bgColor = isError ? 'bg-red-600' : 'bg-green-600';
#                 if (needsConfirmation) bgColor = 'bg-yellow-600';
#                 toast.classList.add(bgColor);
#                 document.body.appendChild(toast);
#                 setTimeout(() => toast.classList.remove('translate-y-20', 'opacity-0'), 10);
#                 setTimeout(() => {
#                     toast.classList.add('translate-y-20', 'opacity-0');
#                     setTimeout(() => toast.remove(), 300);
#                 }, 3000);
#             };

#             // --- STATE MANAGEMENT ---
#             const saveState = () => {
#                 try {
#                     const state = {
#                         tasks,
#                         projectGroups,
#                         viewMode,
#                         projectTitle: projectTitleEl.value,
#                         projectSubtitle: projectSubtitleEl.value,
#                         columnWidths,
#                     };
#                     localStorage.setItem('ganttChartState', JSON.stringify(state));
#                 } catch (e) { console.error("Failed to save state to localStorage", e); }
#             };
            
#             const loadState = () => {
#                 const defaultWidths = { group: 150, taskName: 250, deps: 100 };
#                 const initialStateEl = document.getElementById('initial-state-data');
#                 if (initialStateEl) {
#                     const initialState = JSON.parse(initialStateEl.textContent);
#                     tasks = initialState.tasks || [];
#                     projectGroups = initialState.projectGroups || [];
#                     viewMode = initialState.viewMode || 'day';
#                     projectTitleEl.value = initialState.projectTitle || 'Project Timeline';
#                     projectSubtitleEl.value = initialState.projectSubtitle || 'Interactive Gantt Chart';
#                     columnWidths = initialState.columnWidths || defaultWidths;
#                     viewModeSelect.value = viewMode;
#                     initialStateEl.remove();
#                     saveState(); 
#                     return; 
#                 }

#                 try {
#                     const savedState = localStorage.getItem('ganttChartState');
#                     if (savedState) {
#                         const state = JSON.parse(savedState);
#                         tasks = state.tasks || [];
#                         projectGroups = state.projectGroups || [];
#                         viewMode = state.viewMode || 'day';
#                         projectTitleEl.value = state.projectTitle || 'Project Timeline';
#                         projectSubtitleEl.value = state.projectSubtitle || 'Interactive Gantt Chart';
#                         columnWidths = state.columnWidths || defaultWidths;
#                         viewModeSelect.value = viewMode;
#                     }
#                 } catch (e) {
#                     console.error("Failed to load state from localStorage", e);
#                     localStorage.removeItem('ganttChartState');
#                 }
#             };

#             const clearState = () => {
#                 showToast("Are you sure? This will delete all data. Click again to confirm.", false, true);
#                 clearDataBtn.onclick = () => {
#                     localStorage.removeItem('ganttChartState');
#                     tasks = [];
#                     projectGroups = [];
#                     projectTitleEl.value = "Project Timeline";
#                     projectSubtitleEl.value = "Interactive Gantt Chart";
#                     viewMode = 'day';
#                     viewModeSelect.value = 'day';
#                     columnWidths = { group: 150, taskName: 250, deps: 100 };
#                     renderGanttChart();
#                     showToast("All local data has been cleared.");
#                     clearDataBtn.onclick = clearState;
#                 };
#                 setTimeout(() => { clearDataBtn.onclick = clearState; }, 3000);
#             };

#             // --- DEPENDENCY LOGIC ---
#             const showDependencyModal = (updatePlan, text, onConfirm, onCancel) => {
#                 dependencyModalText.textContent = text;
#                 dependentTasksListEl.innerHTML = updatePlan.map(d => `<p class="p-2 bg-gray-100 rounded-md">#${d.id}: ${d.name}</p>`).join('');
#                 dependencyModal.classList.remove('hidden');
#                 dependencyModal.classList.add('flex');

#                 const cleanup = () => {
#                     dependencyModal.classList.add('hidden');
#                     dependencyModal.classList.remove('flex');
#                     confirmDependencyUpdateBtn.removeEventListener('click', confirmHandler);
#                     cancelDependencyUpdateBtn.removeEventListener('click', cancelHandler);
#                 };

#                 const confirmHandler = () => {
#                     cleanup();
#                     onConfirm();
#                 };
#                 const cancelHandler = () => {
#                     cleanup();
#                     onCancel();
#                 };

#                 confirmDependencyUpdateBtn.addEventListener('click', confirmHandler, { once: true });
#                 cancelDependencyUpdateBtn.addEventListener('click', cancelHandler, { once: true });
#             };

#             const getDependencyUpdatePlan = (parentTask, proposedParentEndDate) => {
#                 const updatePlan = new Map();
#                 const queue = [{ taskId: parentTask.id, newEndDate: proposedParentEndDate }];
#                 const processed = new Set([parentTask.id]);

#                 while (queue.length > 0) {
#                     const { taskId, newEndDate } = queue.shift();

#                     const children = tasks.filter(t => t.dependencies?.split(',').map(d => parseInt(d.trim())).includes(taskId));

#                     for (const child of children) {
#                         const allParentIds = child.dependencies.split(',').map(d => parseInt(d.trim()));
#                         let latestParentEndDate = null;

#                         for (const parentId of allParentIds) {
#                             let parentEndDate;
#                             if (parentId === taskId) {
#                                 parentEndDate = newEndDate;
#                             } else if (updatePlan.has(parentId)) {
#                                 parentEndDate = parseDate(updatePlan.get(parentId).end);
#                             } else {
#                                 const parentTaskData = tasks.find(t => t.id === parentId);
#                                 parentEndDate = parentTaskData ? parseDate(parentTaskData.end) : null;
#                             }

#                             if (!latestParentEndDate || (parentEndDate && parentEndDate > latestParentEndDate)) {
#                                 latestParentEndDate = parentEndDate;
#                             }
#                         }
                        
#                         if (latestParentEndDate) {
#                             const requiredChildStartDate = addDays(latestParentEndDate, 1);
#                             const currentChildStartDate = parseDate(child.start);
                            
#                             if (requiredChildStartDate.getTime() !== currentChildStartDate.getTime()) {
#                                 const duration = dayDiff(child.start, child.end);
#                                 const newChildStartDate = requiredChildStartDate;
#                                 const newChildEndDate = addDays(newChildStartDate, duration);

#                                 if (!updatePlan.has(child.id)) {
#                                      updatePlan.set(child.id, {
#                                         ...child,
#                                         start: formatDateToDDMMYYYY(newChildStartDate),
#                                         end: formatDateToDDMMYYYY(newChildEndDate),
#                                     });
#                                      if (!processed.has(child.id)) {
#                                         queue.push({ taskId: child.id, newEndDate: newChildEndDate });
#                                         processed.add(child.id);
#                                     }
#                                 }
#                             }
#                         }
#                     }
#                 }
#                 return Array.from(updatePlan.values());
#             };

#             // --- COLUMN RESIZING LOGIC ---
#             const initColumnResizing = () => {
#                 document.removeEventListener('mousemove', handleResizeMove);
#                 document.removeEventListener('mouseup', handleResizeEnd);
#                 document.querySelectorAll('.resizer').forEach(resizer => {
#                     resizer.addEventListener('mousedown', handleResizeStart);
#                 });
#             };

#             const handleResizeStart = (e) => {
#                 e.preventDefault();
#                 isResizing = true;
#                 resizingColumn = e.target.dataset.column;
#                 dragStartPos = e.clientX;
#                 document.body.style.cursor = 'col-resize';
#                 document.addEventListener('mousemove', handleResizeMove);
#                 document.addEventListener('mouseup', handleResizeEnd);
#             };

#             const handleResizeMove = (e) => {
#                 if (!isResizing) return;
#                 const deltaX = e.clientX - dragStartPos;
#                 const newWidth = columnWidths[resizingColumn] + deltaX;
#                 if (newWidth > 50) { // Minimum width
#                     document.documentElement.style.setProperty(`--${resizingColumn}-width`, `${newWidth}px`);
#                 }
#             };
            
#             const handleResizeEnd = (e) => {
#                 if (!isResizing) return;
#                 isResizing = false;
#                 const deltaX = e.clientX - dragStartPos;
#                 const newWidth = columnWidths[resizingColumn] + deltaX;
#                 if (newWidth > 50) {
#                     columnWidths[resizingColumn] = newWidth;
#                 }
#                 document.documentElement.style.setProperty(`--${resizingColumn}-width`, `${columnWidths[resizingColumn]}px`);
#                 document.body.style.cursor = 'default';
#                 document.removeEventListener('mousemove', handleResizeMove);
#                 document.removeEventListener('mouseup', handleResizeEnd);
#                 saveState();
#                 renderGanttChart();
#             };

#             // --- DRAG-AND-DROP LOGIC ---
#             const initDragAndDrop = () => {
#                 document.removeEventListener('mousemove', handleDragMove);
#                 document.removeEventListener('mouseup', handleDragEnd);

#                 ganttChartEl.querySelectorAll('.gantt-bar-wrapper').forEach(barWrapper => {
#                     const taskId = barWrapper.dataset.taskBarId;
#                     const taskBar = barWrapper.querySelector('.gantt-bar-bg');
#                     if (!barWrapper.querySelector('.gantt-bar-handle.left')) {
#                         const leftHandle = document.createElement('div');
#                         leftHandle.className = 'gantt-bar-handle left rounded-l-md';
#                         leftHandle.dataset.handleType = 'resize-left';
#                         barWrapper.appendChild(leftHandle);
#                         const rightHandle = document.createElement('div');
#                         rightHandle.className = 'gantt-bar-handle right rounded-r-md';
#                         rightHandle.dataset.handleType = 'resize-right';
#                         barWrapper.appendChild(rightHandle);
#                     }
#                     const handleMouseDown = (e) => {
#                         e.stopPropagation();
#                         if (isResizing) return;
#                         isDragging = true;
#                         currentTaskId = parseInt(taskId);
#                         dragStartPos = e.clientX;
#                         originalTaskData = { ...tasks.find(t => t.id === currentTaskId) };
#                         dragStartStyles = { left: barWrapper.offsetLeft, width: barWrapper.offsetWidth };
#                         dragType = e.target.dataset.handleType || 'move'; 
#                         document.body.classList.add('select-none');
#                         barWrapper.style.zIndex = 30;
#                     };
#                     taskBar.addEventListener('mousedown', handleMouseDown);
#                     barWrapper.querySelector('.gantt-bar-handle.left').addEventListener('mousedown', handleMouseDown);
#                     barWrapper.querySelector('.gantt-bar-handle.right').addEventListener('mousedown', handleMouseDown);
#                 });

#                 document.addEventListener('mousemove', handleDragMove);
#                 document.addEventListener('mouseup', handleDragEnd);
#             };

#             const handleDragMove = (e) => {
#                 if (!isDragging) return;
#                 e.preventDefault();
#                 const barWrapper = ganttChartEl.querySelector(`.gantt-bar-wrapper[data-task-bar-id="${currentTaskId}"]`);
#                 if (!barWrapper) return;
#                 const deltaX = e.clientX - dragStartPos;
#                 if (dragType === 'move') {
#                     barWrapper.style.left = `${dragStartStyles.left + deltaX}px`;
#                 } else if (dragType === 'resize-right') {
#                     const newWidth = dragStartStyles.width + deltaX;
#                     if (newWidth > pixelsPerDay / 2) { barWrapper.style.width = `${newWidth}px`; }
#                 } else if (dragType === 'resize-left') {
#                     const newWidth = dragStartStyles.width - deltaX;
#                     if (newWidth > pixelsPerDay / 2) {
#                         barWrapper.style.left = `${dragStartStyles.left + deltaX}px`;
#                         barWrapper.style.width = `${newWidth}px`;
#                     }
#                 }
#                 drawDependencyArrows();
#             };

#             const handleDragEnd = (e) => {
#                 if (!isDragging || !currentTaskId) return;
                
#                 const task = tasks.find(t => t.id === currentTaskId);
#                 if (!task) { isDragging = false; return; }

#                 document.body.classList.remove('select-none');
                
#                 const barWrapper = ganttChartEl.querySelector(`.gantt-bar-wrapper[data-task-bar-id="${currentTaskId}"]`);
#                 if (barWrapper) barWrapper.style.zIndex = 10;
                
#                 isDragging = false;
#                 const finalDayShift = Math.round((e.clientX - dragStartPos) / pixelsPerDay);

#                 if (finalDayShift === 0 && dragType !== 'resize-left' && dragType !== 'resize-right') {
#                     renderGanttChart();
#                     return;
#                 }
                
#                 const updatedTaskData = { ...task };
#                 let newStart, newEnd;
                
#                 if (dragType === 'move') {
#                     newStart = addDays(parseDate(originalTaskData.start), finalDayShift);
#                     newEnd = addDays(newStart, dayDiff(originalTaskData.start, originalTaskData.end));
#                 } else if (dragType === 'resize-right') {
#                     newStart = parseDate(task.start);
#                     newEnd = addDays(parseDate(originalTaskData.end), finalDayShift);
#                     if (newEnd < newStart) newEnd = newStart;
#                 } else {
#                     newEnd = parseDate(task.end);
#                     newStart = addDays(parseDate(originalTaskData.start), finalDayShift);
#                     if (newStart > newEnd) newStart = newEnd;
#                 }

#                 updatedTaskData.start = formatDateToDDMMYYYY(newStart);
#                 updatedTaskData.end = formatDateToDDMMYYYY(newEnd);

#                 const updatePlan = getDependencyUpdatePlan(task, parseDate(updatedTaskData.end));

#                 const performUpdate = () => {
#                     const taskIndex = tasks.findIndex(t => t.id === currentTaskId);
#                     if(taskIndex !== -1) tasks[taskIndex] = updatedTaskData;
                    
#                     updatePlan.forEach(plannedUpdate => {
#                         const childIndex = tasks.findIndex(t => t.id === plannedUpdate.id);
#                         if (childIndex !== -1) {
#                             tasks[childIndex].start = plannedUpdate.start;
#                             tasks[childIndex].end = plannedUpdate.end;
#                         }
#                     });
#                     renderGanttChart();
#                     saveState();
#                 };

#                 if (updatePlan.length > 0) {
#                     const dateShift = dayDiff(originalTaskData.start, updatedTaskData.start);
#                     const direction = dateShift > 0 ? 'forward' : 'backward';
#                     const modalText = `Shifting this task ${direction} by ${Math.abs(dateShift)} day(s) will also shift ${updatePlan.length} dependent task(s). Do you want to proceed?`;
                    
#                     showDependencyModal(updatePlan, modalText, performUpdate, () => renderGanttChart());
#                 } else {
#                     const taskIndex = tasks.findIndex(t => t.id === currentTaskId);
#                     if(taskIndex !== -1) tasks[taskIndex] = updatedTaskData;
#                     renderGanttChart();
#                     saveState();
#                 }
#                 currentTaskId = null;
#             };
            
#             // --- MODAL & DATA LOGIC ---
#             const saveTask = (e) => {
#                 e.preventDefault();
#                 const id = document.getElementById('task-id').value;
#                 const name = document.getElementById('task-name').value;
#                 const group = document.getElementById('task-group').value;
#                 const startValue = document.getElementById('task-start').value;
#                 const endValue = document.getElementById('task-end').value;
#                 const progress = parseInt(document.getElementById('task-progress').value, 10);
#                 const colorInput = document.getElementById('task-color');
#                 const color = colorInput.disabled ? null : colorInput.value;
#                 const selectedOptions = Array.from(document.getElementById('task-dependencies').selectedOptions);
#                 const dependencies = selectedOptions.map(opt => opt.value).join(',');
                
#                 if (parseDate(startValue) > parseDate(endValue)) {
#                     showToast("End date must be after start date.", true);
#                     return;
#                 }

#                 const finalTaskData = { name, group, start: formatDateToDDMMYYYY(parseDate(startValue)), end: formatDateToDDMMYYYY(parseDate(endValue)), progress, dependencies, color };
                
#                 const performUpdate = (isNew = false, updatePlan = []) => {
#                     if (isNew) {
#                         const newId = tasks.length > 0 ? Math.max(...tasks.map(t => t.id)) + 1 : 1;
#                         tasks.push({ id: newId, ...finalTaskData });
#                     } else {
#                         const taskIndex = tasks.findIndex(t => t.id == id);
#                         if (taskIndex !== -1) tasks[taskIndex] = { ...tasks[taskIndex], ...finalTaskData };
                        
#                         updatePlan.forEach(plannedUpdate => {
#                             const childIndex = tasks.findIndex(t => t.id === plannedUpdate.id);
#                             if (childIndex !== -1) {
#                                 tasks[childIndex].start = plannedUpdate.start;
#                                 tasks[childIndex].end = plannedUpdate.end;
#                             }
#                         });
#                     }
#                     renderGanttChart();
#                     closeModal();
#                     saveState();
#                 };

#                 if (id) {
#                     const task = tasks.find(t => t.id == id);
#                     const updatePlan = getDependencyUpdatePlan(task, parseDate(finalTaskData.end));
                    
#                     if (updatePlan.length > 0) {
#                          const modalText = `Updating this task's dates will shift ${updatePlan.length} dependent task(s). Do you want to proceed?`;
#                          showDependencyModal(updatePlan, modalText, () => performUpdate(false, updatePlan), () => {});
#                     } else {
#                         performUpdate(false);
#                     }
#                 } else {
#                     performUpdate(true);
#                 }
#             };

#             const deleteTask = () => {
#                 const id = document.getElementById('task-id').value;
#                 tasks = tasks.filter(t => t.id != id);
#                 tasks.forEach(task => {
#                     if (task.dependencies) {
#                         const deps = task.dependencies.split(',').map(d => d.trim());
#                         task.dependencies = deps.filter(depId => depId != id).join(',');
#                     }
#                 });
#                 renderGanttChart();
#                 closeModal();
#                 saveState();
#             };
            
#             const openModal = (task = null) => {
#                 taskForm.reset();
#                 delete taskForm.dataset.duration;
#                 document.getElementById('task-end').min = '';
#                 const taskId = task ? task.id : null;
#                 const depsSelect = document.getElementById('task-dependencies');
#                 depsSelect.innerHTML = '';
#                 tasks.forEach(t => {
#                     if (t.id !== taskId) {
#                         const option = document.createElement('option');
#                         option.value = t.id;
#                         option.textContent = `#${t.id}: ${t.name}`;
#                         depsSelect.appendChild(option);
#                     }
#                 });
#                 const groupSelect = document.getElementById('task-group');
#                 groupSelect.innerHTML = `<option value="">-- No Group --</option>`;
#                 projectGroups.forEach(group => {
#                     const option = document.createElement('option');
#                     option.value = group.name;
#                     option.textContent = group.name;
#                     groupSelect.appendChild(option);
#                 });
#                 if (task) {
#                     document.getElementById('modal-title').textContent = 'Edit Task';
#                     document.getElementById('task-id').value = task.id;
#                     document.getElementById('task-name').value = task.name;
#                     groupSelect.value = task.group || '';
#                     document.getElementById('task-start').value = formatDateToYYYYMMDD(parseDate(task.start));
#                     document.getElementById('task-end').value = formatDateToYYYYMMDD(parseDate(task.end));
#                     document.getElementById('task-end').min = formatDateToYYYYMMDD(parseDate(task.start));
#                     document.getElementById('task-progress').value = task.progress;
#                     document.getElementById('progress-value').textContent = task.progress;
#                     document.getElementById('delete-task-btn').classList.remove('hidden');
#                     taskForm.dataset.duration = dayDiff(task.start, task.end);
#                     if (task.dependencies) {
#                         const depIds = task.dependencies.split(',').map(d => d.trim());
#                         for (const option of depsSelect.options) {
#                             if (depIds.includes(option.value)) option.selected = true;
#                         }
#                     }
#                 } else {
#                     document.getElementById('modal-title').textContent = 'Add New Task';
#                     document.getElementById('task-id').value = '';
#                     document.getElementById('progress-value').textContent = '0';
#                     document.getElementById('delete-task-btn').classList.add('hidden');
#                 }
#                 updateColorPickerState();
#                 taskModal.classList.remove('hidden');
#                 taskModal.classList.add('flex');
#             };

#             const closeModal = () => {
#                 taskModal.classList.add('hidden');
#                 taskModal.classList.remove('flex');
#             };

#             const updateColorPickerState = () => {
#                 const groupSelect = document.getElementById('task-group');
#                 const colorInput = document.getElementById('task-color');
#                 const selectedGroup = projectGroups.find(g => g.name === groupSelect.value);
#                 if (selectedGroup) {
#                     colorInput.value = selectedGroup.color;
#                     colorInput.disabled = true;
#                 } else {
#                     colorInput.disabled = false;
#                     const taskId = document.getElementById('task-id').value;
#                     const currentTask = tasks.find(t => t.id == taskId);
#                     if (currentTask && !currentTask.group && currentTask.color) {
#                         colorInput.value = currentTask.color;
#                     }
#                 }
#             };

#             const openGroupModal = () => {
#                 renderGroupList();
#                 groupModal.classList.remove('hidden');
#                 groupModal.classList.add('flex');
#             };

#             const closeGroupModal = () => {
#                 groupModal.classList.add('hidden');
#                 groupModal.classList.remove('flex');
#             };

#             const renderGroupList = () => {
#                 groupListEl.innerHTML = '';
#                 if (projectGroups.length === 0) {
#                     groupListEl.innerHTML = `<p class="text-sm text-gray-500">No groups defined yet.</p>`;
#                     return;
#                 }
#                 projectGroups.forEach(group => {
#                     const groupEl = document.createElement('div');
#                     groupEl.className = 'flex items-center justify-between p-2 bg-gray-50 rounded-lg';
#                     groupEl.innerHTML = `<div class="flex items-center gap-3"><div class="w-5 h-5 rounded-full" style="background-color: ${group.color};"></div><span class="font-medium text-gray-800">${group.name}</span></div><button data-group-name="${group.name}" class="text-gray-400 hover:text-red-600 delete-group-btn">&times;</button>`;
#                     groupListEl.appendChild(groupEl);
#                 });
#                 groupListEl.querySelectorAll('.delete-group-btn').forEach(btn => {
#                     btn.addEventListener('click', () => deleteGroup(btn.dataset.groupName));
#                 });
#             };

#             const addGroup = (e) => {
#                 e.preventDefault();
#                 const nameInput = document.getElementById('new-group-name');
#                 const colorInput = document.getElementById('new-group-color');
#                 const name = nameInput.value.trim();
#                 if (!name) {
#                     showToast("Group name cannot be empty.", true);
#                     return;
#                 }
#                 if (projectGroups.some(g => g.name.toLowerCase() === name.toLowerCase())) {
#                     showToast("A group with this name already exists.", true);
#                     return;
#                 }
#                 projectGroups.push({
#                     name,
#                     color: colorInput.value
#                 });
#                 addGroupForm.reset();
#                 colorInput.value = '#79D3C9';
#                 renderGroupList();
#                 saveState();
#             };

#             const deleteGroup = (groupName) => {
#                 projectGroups = projectGroups.filter(g => g.name !== groupName);
#                 tasks.forEach(task => {
#                     if (task.group === groupName) {
#                         task.group = '';
#                     }
#                 });
#                 renderGroupList();
#                 renderGanttChart();
#                 saveState();
#             };

#             const downloadAsExcel = () => {
#                 const workbook = XLSX.utils.book_new();
#                 const projectInfoData = [
#                     ['Project Title', projectTitleEl.value],
#                     ['Project Subtitle', projectSubtitleEl.value]
#                 ];
#                 const projectInfoWorksheet = XLSX.utils.aoa_to_sheet(projectInfoData);
#                 projectInfoWorksheet['!cols'] = [{ wch: 20 }, { wch: 50 }];
#                 XLSX.utils.book_append_sheet(workbook, projectInfoWorksheet, "ProjectInfo");
#                 if (projectGroups.length > 0) {
#                     const groupsWorksheet = XLSX.utils.json_to_sheet(projectGroups);
#                     groupsWorksheet['!cols'] = [{ wch: 25 }, { wch: 10 }];
#                     XLSX.utils.book_append_sheet(workbook, groupsWorksheet, "Groups");
#                 }
#                 const tasksExportData = tasks.map(({ id, name, group, start, end, progress, dependencies, color }) => ({
#                     'Group': group || '',
#                     'Task Name': name,
#                     'ID': id,
#                     'Start Date': start,
#                     'End Date': end,
#                     'Progress (%)': progress,
#                     'Dependencies': dependencies || '',
#                     'Color': color || ''
#                 }));
#                 const tasksWorksheet = XLSX.utils.json_to_sheet(tasksExportData);
#                 tasksWorksheet['!cols'] = [{ wch: 20 }, { wch: 40 }, { wch: 5 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 15 }, { wch: 10 }];
#                 XLSX.utils.book_append_sheet(workbook, tasksWorksheet, "Tasks");
#                 const safeFilename = projectTitleEl.value.replace(/[^a-z0-9]/gi, '_').toLowerCase() || 'gantt_chart';
#                 XLSX.writeFile(workbook, `${safeFilename}.xlsx`);
#             };
            
#             const downloadAsHtml = () => {
#                 const htmlContent = document.documentElement.cloneNode(true);
#                 const currentState = {
#                     tasks,
#                     projectGroups,
#                     viewMode,
#                     projectTitle: projectTitleEl.value,
#                     projectSubtitle: projectSubtitleEl.value,
#                     columnWidths
#                 };
#                 const stateScript = document.createElement('script');
#                 stateScript.id = 'initial-state-data';
#                 stateScript.type = 'application/json';
#                 stateScript.textContent = JSON.stringify(currentState);
#                 const existingState = htmlContent.querySelector('#initial-state-data');
#                 if (existingState) existingState.remove();
#                 htmlContent.querySelector('body').prepend(stateScript);
#                 const blob = new Blob([htmlContent.outerHTML], {
#                     type: 'text/html'
#                 });
#                 const url = URL.createObjectURL(blob);
#                 const a = document.createElement('a');
#                 const safeFilename = projectTitleEl.value.replace(/[^a-z0-9]/gi, '_').toLowerCase() || 'gantt_chart';
#                 a.download = `${safeFilename}.html`;
#                 a.href = url;
#                 a.style.display = 'none';
#                 document.body.appendChild(a);
#                 a.click();
#                 document.body.removeChild(a);
#                 URL.revokeObjectURL(url);
#             };

#             const handleFileUpload = (event) => {
#                 const file = event.target.files[0];
#                 if (!file) return;
#                 const reader = new FileReader();
#                 reader.onload = (e) => {
#                     try {
#                         const data = new Uint8Array(e.target.result);
#                         const workbook = XLSX.read(data, {
#                             type: 'array',
#                             cellDates: true
#                         });
#                         if (workbook.SheetNames.includes("ProjectInfo")) {
#                             const worksheet = workbook.Sheets["ProjectInfo"];
#                             const infoJson = XLSX.utils.sheet_to_json(worksheet, {
#                                 header: 1
#                             });
#                             const titleRow = infoJson.find(row => row[0] === 'Project Title');
#                             const subtitleRow = infoJson.find(row => row[0] === 'Project Subtitle');
#                             if (titleRow && titleRow[1]) projectTitleEl.value = titleRow[1];
#                             if (subtitleRow && subtitleRow[1]) projectSubtitleEl.value = subtitleRow[1];
#                         }
#                         projectGroups = [];
#                         if (workbook.SheetNames.includes("Groups")) {
#                             const worksheet = workbook.Sheets["Groups"];
#                             projectGroups = XLSX.utils.sheet_to_json(worksheet);
#                         }
#                         const tasksSheetName = workbook.SheetNames.includes("Tasks") ? "Tasks" : workbook.SheetNames[0];
#                         const worksheet = workbook.Sheets[tasksSheetName];
#                         if (!worksheet) throw new Error("No task data sheet found.");
#                         const json = XLSX.utils.sheet_to_json(worksheet, {
#                             header: 1
#                         });
#                         const headers = json[0].map(h => String(h).trim());
#                         const idx = Object.fromEntries(headers.map(h => [h, headers.indexOf(h)]));
#                         tasks = json.slice(1).map((row, i) => {
#                             const start = row[idx['Start Date']];
#                             const end = row[idx['End Date']];
#                             return {
#                                 id: row[idx['ID']] ? parseInt(row[idx['ID']]) : i + 1,
#                                 name: String(row[idx['Task Name']] || ''),
#                                 group: String(row[idx['Group']] || ''),
#                                 start: start instanceof Date ? formatDateToDDMMYYYY(start) : String(start || ''),
#                                 end: end instanceof Date ? formatDateToDDMMYYYY(end) : String(end || ''),
#                                 progress: parseInt(row[idx['Progress (%)']] || 0),
#                                 dependencies: String(row[idx['Dependencies']] || ''),
#                                 color: row[idx['Color']] ? String(row[idx['Color']]) : null
#                             };
#                         }).filter(t => t.name && t.start && t.end);
#                         viewModeSelect.value = 'day';
#                         renderGanttChart();
#                         saveState();
#                         showToast('Successfully imported project data!');
#                     } catch (error) {
#                         showToast(error.message, true);
#                     } finally {
#                         event.target.value = '';
#                     }
#                 };
#                 reader.readAsArrayBuffer(file);
#             };

#             // --- MAIN RENDER FUNCTION ---
#             const renderGanttChart = () => {
#                 if (!ganttChartEl) return;
#                 const scrollLeft = ganttChartContainerEl.scrollLeft;
#                 const scrollTop = ganttChartContainerEl.scrollTop;
#                 ganttChartEl.innerHTML = ''; 
#                 dependencyLinesEl.innerHTML = '';
#                 document.documentElement.style.setProperty('--group-width', `${columnWidths.group}px`);
#                 document.documentElement.style.setProperty('--task-name-width', `${columnWidths.taskName}px`);
#                 document.documentElement.style.setProperty('--deps-width', `${columnWidths.deps}px`);
#                 if (tasks.length === 0) {
#                     ganttChartEl.innerHTML = `<div class="text-center p-10 text-gray-500 col-span-full">No tasks yet. Click '+ Add Task' to begin.</div>`;
#                     return;
#                 }
#                 const groupColors = Object.fromEntries(projectGroups.map(g => [g.name, g.color]));
#                 tasks.sort((a, b) => (a.group || 'zzzz').localeCompare(b.group || 'zzzz') || parseDate(a.start) - parseDate(b.start));
#                 const allDates = tasks.flatMap(t => [parseDate(t.start), parseDate(t.end)]).filter(d => d && !isNaN(d));
#                 if (allDates.length === 0) {
#                     ganttChartEl.innerHTML = `<div class="text-center p-10 text-gray-500 col-span-full">No valid dates found in tasks.</div>`;
#                     return;
#                 };
#                 chartStartDate = addDays(new Date(Math.min(...allDates)), -2);
#                 let chartEndDate = addDays(new Date(Math.max(...allDates)), 2);
#                 let headers = [];
#                 const columnWidth = viewMode === 'day' ? 40 : viewMode === 'week' ? 60 : viewMode === 'month' ? 80 : 120;
#                 if (viewMode === 'day') {
#                     let d = new Date(chartStartDate);
#                     while (d <= chartEndDate) {
#                         headers.push({
#                             label: d.getUTCDate(),
#                             subLabel: d.getUTCDate() === 1 || headers.length === 0 ? d.toLocaleString('default', { month: 'short', timeZone: 'UTC' }) : '',
#                             isWeekend: [0, 6].includes(d.getUTCDay()),
#                             startDate: new Date(d),
#                             days: 1
#                         });
#                         d = addDays(d, 1);
#                     }
#                 } else {
#                      let unitStartDate = new Date(chartStartDate);
#                     while (unitStartDate <= chartEndDate) {
#                         let unitEndDate, label, subLabel;
#                         const year = unitStartDate.getUTCFullYear();
#                         if (viewMode === 'week') {
#                             const dayOfWeek = unitStartDate.getUTCDay();
#                             const startOfWeek = addDays(unitStartDate, -dayOfWeek);
#                             unitEndDate = addDays(startOfWeek, 6);
#                             const weekNum = Math.ceil(( (startOfWeek - new Date(Date.UTC(year, 0, 1))) / 86400000 + 1) / 7);
#                             label = `W${weekNum}`;
#                             subLabel = `${startOfWeek.getUTCDate()}/${startOfWeek.getUTCMonth() + 1}`;

#                         } else if (viewMode === 'month') {
#                             unitStartDate = new Date(Date.UTC(year, unitStartDate.getUTCMonth(), 1));
#                             unitEndDate = new Date(Date.UTC(year, unitStartDate.getUTCMonth() + 1, 0));
#                             label = unitStartDate.toLocaleString('default', { month: 'short', year: 'numeric', timeZone: 'UTC' });
#                         } else if (viewMode === 'quarter') {
#                             const q = Math.floor(unitStartDate.getUTCMonth() / 3);
#                             unitStartDate = new Date(Date.UTC(year, q * 3, 1));
#                             unitEndDate = new Date(Date.UTC(year, unitStartDate.getUTCMonth() + 3, 0));
#                             label = `Q${q + 1} ${year}`;
#                         } else if (viewMode === 'year') {
#                             unitStartDate = new Date(Date.UTC(year, 0, 1));
#                             unitEndDate = new Date(Date.UTC(year, 11, 31));
#                             label = year;
#                         }
#                         headers.push({
#                             label, subLabel,
#                             startDate: new Date(unitStartDate),
#                             days: dayDiff(formatDateToYYYYMMDD(unitStartDate), formatDateToYYYYMMDD(unitEndDate)) + 1
#                         });
#                         unitStartDate = addDays(unitEndDate, 1);
#                     }
#                     chartStartDate = headers[0].startDate;
#                 }
#                 const finalChartEndDate = addDays(headers[headers.length - 1].startDate, headers[headers.length - 1].days);
#                 const totalChartDays = dayDiff(formatDateToYYYYMMDD(chartStartDate), formatDateToYYYYMMDD(finalChartEndDate));
#                 const frozenWidth = columnWidths.group + columnWidths.taskName + columnWidths.deps;
#                 const timelineContainerWidth = ganttChartContainerEl.offsetWidth - frozenWidth;
#                 const totalTimelinePixelWidth = Math.max(timelineContainerWidth, headers.length * columnWidth);
#                 pixelsPerDay = totalTimelinePixelWidth / totalChartDays;
#                 ganttChartEl.style.gridTemplateColumns = `var(--group-width) var(--task-name-width) var(--deps-width) repeat(${headers.length}, 1fr)`;
#                 ganttChartEl.style.width = `${frozenWidth + totalTimelinePixelWidth}px`;
#                 const createHeaderCell = (content, col, stickyLeft, hasResizer = false) => {
#                     const cell = document.createElement('div');
#                     cell.className = 'sticky top-0 z-20 bg-gray-100 p-3 font-semibold text-sm border-b border-r border-gray-200 flex items-center justify-between relative';
#                     cell.style.gridColumn = col;
#                     cell.innerHTML = content;
#                     if (stickyLeft !== null) cell.style.left = stickyLeft;
#                     if (hasResizer) cell.innerHTML += `<div class="resizer" data-column="${hasResizer}"></div>`;
#                     return cell;
#                 }
#                 const groupHeader = createHeaderCell('Group', '1', '0px', 'group');
#                 groupHeader.classList.add('z-30');
#                 ganttChartEl.appendChild(groupHeader);
#                 ganttChartEl.appendChild(createHeaderCell('Task Name', '2', 'var(--group-width)', 'taskName'));
#                 ganttChartEl.appendChild(createHeaderCell('Depends On', '3', 'calc(var(--group-width) + var(--task-name-width))'));
#                 headers.forEach((h, i) => {
#                     const cell = document.createElement('div');
#                     cell.className = `sticky top-0 z-10 text-center border-b border-l border-gray-200 text-xs text-gray-500 ${h.isWeekend ? 'bg-gray-200/50' : 'bg-gray-100/50'}`;
#                     cell.style.cssText = `grid-column: ${i+4}; height:${taskRowHeight}px; display:flex; flex-direction:column; justify-content:center;`;
#                     cell.innerHTML = `${h.subLabel ? `<div class="text-gray-700 font-medium">${h.subLabel}</div>` : ''}<div>${h.label}</div>`;
#                     ganttChartEl.appendChild(cell);
#                 });
#                 tasks.forEach((task, taskIndex) => {
#                     const createDataCell = (content, col, stickyLeft) => {
#                         const cell = document.createElement('div');
#                         cell.className = 'sticky z-10 bg-white p-3 border-b border-r border-gray-200 text-sm truncate';
#                         cell.style.cssText = `grid-row: ${taskIndex+2}; grid-column: ${col}; left: ${stickyLeft};`;
#                         cell.textContent = content;
#                         return cell;
#                     }
#                     ganttChartEl.appendChild(createDataCell(task.group || '', '1', '0px'));
                    
#                     const taskNameCell = createDataCell(task.name, '2', 'var(--group-width)');
#                     taskNameCell.classList.add('hover:bg-gray-50', 'cursor-pointer');
#                     taskNameCell.title = `Click to edit task: "${task.name}"`;
#                     taskNameCell.addEventListener('click', () => openModal(task));
#                     ganttChartEl.appendChild(taskNameCell);

#                     ganttChartEl.appendChild(createDataCell(task.dependencies || '', '3', 'calc(var(--group-width) + var(--task-name-width))'));
#                     const timelineCell = document.createElement('div');
#                     timelineCell.className = 'relative border-b border-gray-200 task-row-timeline';
#                     timelineCell.style.cssText = `grid-row: ${taskIndex+2}; grid-column: 4 / -1;`;
#                     const startPos = dayDiff(formatDateToYYYYMMDD(chartStartDate), task.start) * pixelsPerDay;
#                     const barDurationDays = dayDiff(task.start, task.end);
#                     const barWidth = (barDurationDays + 1) * pixelsPerDay;
#                     const barColor = task.color || groupColors[task.group] || '#79D3C9';
#                     timelineCell.innerHTML = `<div class="gantt-bar-wrapper" data-task-bar-id="${task.id}" style="position: absolute; left: ${startPos}px; width: ${barWidth}px; top:0; height: 100%"><div class="absolute top-1/2 -translate-y-1/2 left-0 w-full h-3/5 rounded-md gantt-bar-bg shadow-sm" style="background-color: ${barColor}40;"><div class="h-full rounded-md gantt-bar-progress" style="width: ${task.progress}%; background-color: ${barColor};"></div></div><div class="gantt-tooltip absolute bottom-full mb-2 w-max max-w-xs p-3 rounded-lg shadow-lg text-sm z-30" style="background-color: #006152; color: white;"><div class="font-bold">#${task.id}: ${task.name}</div><div>${task.start} to ${task.end}</div><div>Duration: ${barDurationDays + 1} days</div><div>Progress: <span class="font-semibold">${task.progress}%</span></div></div></div>`;
                    
#                     timelineCell.addEventListener('click', (e) => {
#                         if (!e.target.closest('.gantt-bar-wrapper')) {
#                             openModal(task);
#                         }
#                     });
                    
#                     ganttChartEl.appendChild(timelineCell);

#                     timelineCell.querySelector('.gantt-bar-wrapper')?.addEventListener('contextmenu', (e) => {
#                         e.preventDefault();
#                         openModal(task);
#                     });
#                 });
#                 initDragAndDrop();
#                 initColumnResizing();
#                 ganttChartContainerEl.scrollLeft = scrollLeft;
#                 ganttChartContainerEl.scrollTop = scrollTop;
#                 setTimeout(() => drawDependencyArrows(), 50);
#             };

#             const drawDependencyArrows = () => {
#                 if (tasks.length === 0) return;
#                 dependencyLinesEl.innerHTML = `<defs><marker id="arrow-head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#006152" opacity="0.8"></path></marker><marker id="arrow-head-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#DC2626" opacity="0.8"></path></marker></defs>`;
#                 dependencyLinesEl.style.width = `${ganttChartEl.scrollWidth}px`;
#                 dependencyLinesEl.style.height = `${ganttChartEl.scrollHeight}px`;
                
#                 tasks.forEach(task => {
#                     if (!task.dependencies) return;
#                     const childBarWrapper = ganttChartEl.querySelector(`.gantt-bar-wrapper[data-task-bar-id="${task.id}"]`);
#                     if (!childBarWrapper) return;
#                     const childTimelineCell = childBarWrapper.closest('.task-row-timeline');
#                     if (!childTimelineCell) return;
#                     const childRowTop = childTimelineCell.offsetTop;
#                     const endY = childRowTop + (childTimelineCell.offsetHeight / 2);
#                     const endX = childTimelineCell.offsetLeft + childBarWrapper.offsetLeft;
#                     task.dependencies.split(',').forEach(depId => {
#                         const parentBarWrapper = ganttChartEl.querySelector(`.gantt-bar-wrapper[data-task-bar-id="${depId.trim()}"]`);
#                         if (!parentBarWrapper) return;
#                         const parentTimelineCell = parentBarWrapper.closest('.task-row-timeline');
#                         if (!parentTimelineCell) return;
#                         const parentRowTop = parentTimelineCell.offsetTop;
#                         const startY = parentRowTop + (parentTimelineCell.offsetHeight / 2);
#                         const startX = parentTimelineCell.offsetLeft + parentBarWrapper.offsetLeft + parentBarWrapper.offsetWidth;
#                         const neck = 15;
#                         const pathD = `M ${startX} ${startY} H ${startX + neck} V ${endY} H ${endX}`;
#                         const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
#                         path.setAttribute('d', pathD);
#                         const isConflict = endX < startX;
#                         path.setAttribute('stroke', isConflict ? '#DC2626' : '#006152');
#                         path.setAttribute('marker-end', isConflict ? 'url(#arrow-head-red)' : 'url(#arrow-head)');
#                         path.setAttribute('fill', 'none');
#                         path.setAttribute('stroke-width', '1.5');
#                         path.setAttribute('opacity', '0.8');
#                         dependencyLinesEl.appendChild(path);
#                     });
#                 });
#             };

#             // --- INITIALIZATION & EVENT LISTENERS ---
#             const handleStartDateChange = (e) => {
#                 const taskEndInput = document.getElementById('task-end');
#                 const startDate = e.target.value;
#                 if (startDate) {
#                     taskEndInput.min = startDate;
#                     if (taskForm.dataset.duration) {
#                         const duration = parseInt(taskForm.dataset.duration, 10);
#                         const newEndDate = addDays(parseDate(startDate), duration);
#                         taskEndInput.value = formatDateToYYYYMMDD(newEndDate);
#                     } else if (!taskEndInput.value || parseDate(taskEndInput.value) < parseDate(startDate)) {
#                         taskEndInput.value = startDate;
#                     }
#                 }
#             };

#             document.getElementById('task-start').addEventListener('input', handleStartDateChange);
#             document.getElementById('task-end').addEventListener('input', () => { delete taskForm.dataset.duration; });
#             document.getElementById('task-group').addEventListener('change', updateColorPickerState);
#             document.getElementById('task-progress').addEventListener('input', (e) => { document.getElementById('progress-value').textContent = e.target.value; });
#             currentDateEl.textContent = new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date());
#             addTaskBtn.addEventListener('click', () => openModal());
#             cancelBtn.addEventListener('click', closeModal);
#             taskForm.addEventListener('submit', saveTask);
#             deleteTaskBtn.addEventListener('click', deleteTask);
#             downloadBtn.addEventListener('click', downloadAsExcel);
#             downloadHtmlBtn.addEventListener('click', downloadAsHtml);
#             clearDataBtn.addEventListener('click', clearState);
#             printBtn.addEventListener('click', () => window.print());
#             fileInput.addEventListener('change', handleFileUpload);
#             viewModeSelect.addEventListener('change', (e) => { viewMode = e.target.value; saveState(); renderGanttChart(); });
#             manageGroupsBtn.addEventListener('click', openGroupModal);
#             closeGroupModalBtn.addEventListener('click', closeGroupModal);
#             addGroupForm.addEventListener('submit', addGroup);
#             projectTitleEl.addEventListener('change', saveState);
#             projectSubtitleEl.addEventListener('change', saveState);
#             window.addEventListener('resize', renderGanttChart);
#             ganttChartContainerEl.addEventListener('scroll', drawDependencyArrows);
            
#             loadState();
#             renderGanttChart();
#         });
#     </script>

# </body>
# </html>
# """

# # Use Streamlit's component function to render the HTML.
# # The `height` parameter is set to ensure the component has enough space.
# # `scrolling`=True allows the inner content to scroll if it overflows the height.
# components.html(gantt_chart_html, height=800, scrolling=True)

