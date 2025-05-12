import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
} from 'reactflow';

import 'reactflow/dist/style.css';
import './TracerPage.css'; // Specific styles for this page

// --- Dummy Task Graph Data ---
// Matches the structure from TaskGraphGenerator
const dummyTaskGraph = {
  name: "bug_SV-20250411",
  description: "Task graph for JSON Tampering Exploit",
  environment: { application: "ProcureWave v3.2.7" },
  task_graph: {
    nodes: [
      {
        id: "1",
        type: "custom", // Use a custom node type for hover/blinking later
        position: { x: 50, y: 50 },
        data: {
          label: "Step 1: Login & Navigate",
          content: "Log in to ProcureWave. Navigate to 'Purchase Orders'. Select 'Create PO Request'.",
          metadata: { image_refs: [], ui_elements: ['Login Button', 'Purchase Orders Menu', 'Create PO Request Button'], inputs: [], expected_result: "PO creation form is visible" }
        }
      },
      {
        id: "2",
        type: "custom",
        position: { x: 50, y: 150 },
        data: {
          label: "Step 2: Fill PO Form",
          content: "Fill in standard PO fields: Vendor, Items, Cost Center.",
          metadata: { image_refs: [], ui_elements: ['Vendor Field', 'Items Field', 'Cost Center Field'], inputs: ['vendor=ACME', 'item=Widgets'], expected_result: "Form fields populated" }
        }
      },
       {
        id: "3",
        type: "custom",
        position: { x: 50, y: 250 },
        data: {
          label: "Step 3: Setup Intercept",
          content: "Configure Burp Suite (or similar proxy) to intercept POST requests to the /api/purchase_orders endpoint.",
          metadata: { image_refs: [], ui_elements: [], inputs: [], expected_result: "Proxy ready to intercept" }
        }
      },
      {
        id: "4",
        type: "custom",
        position: { x: 300, y: 350 }, // Branching for the vulnerability step
        data: {
          label: "Step 4: Modify JSON",
          content: "Submit PO. In intercepted request, modify JSON: change total_amount to 49999.99, add approval_status: CFO_APPROVED, set cost_center_id: FIN-2023-EXEC.",
          metadata: { image_refs: [], ui_elements: [], inputs: ['total_amount=49999.99', 'approval_status=CFO_APPROVED'], expected_result: "JSON payload modified" }
        }
      },
      {
        id: "5",
        type: "custom",
        position: { x: 300, y: 450 },
        data: {
          label: "Step 5: Forward Request",
          content: "Forward the modified JSON request to ProcureWave.",
          metadata: { image_refs: [], ui_elements: [], inputs: [], expected_result: "Request sent to server" }
        }
      },
      {
        id: "6",
        type: "custom",
        position: { x: 300, y: 550 },
        data: {
          label: "Step 6: Observe Response",
          content: "Server responds with 200 OK, PO #98765.",
          metadata: { image_refs: [], ui_elements: [], inputs: [], expected_result: "Server accepts request, returns PO ID" }
        }
      },
      {
        id: "7",
        type: "custom",
        position: { x: 550, y: 650 }, // Verification steps
        data: {
          label: "Step 7-8: Verification",
          content: "Navigate to PO Dashboard. Verify PO #98765 shows as 'CFO_APPROVED' with $49,999.99.",
          metadata: { image_refs: [], ui_elements: ['PO Dashboard', 'PO #98765 Entry'], inputs: [], expected_result: "Bug is verified: PO shows incorrect amount and status" }
        }
      },
    ],
    edges: [
      { id: 'e1-2', source: '1', target: '2', animated: true },
      { id: 'e2-3', source: '2', target: '3', animated: true },
      { id: 'e3-4', source: '3', target: '4', animated: true },
      { id: 'e4-5', source: '4', target: '5', animated: true },
      { id: 'e5-6', source: '5', target: '6', animated: true },
      { id: 'e6-7', source: '6', target: '7', animated: true },
    ]
  },
  verification_steps: ["Verify PO #98765 shows CFO_APPROVED with $49,999.99"],
  confidence_score: 0.95,
  missing_information: []
};
// --- End Dummy Task Graph Data ---

// --- Dummy Simulation Logic ---
const simulationSteps = dummyTaskGraph.task_graph.nodes.map(n => n.id);
const SIMULATION_DELAY = 2500; // ms between steps
// --- End Dummy Simulation Logic ---

// Custom Node for potential styling/interactions
const CustomNode = ({ data }) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div
      className={`custom-node ${data.isCurrent ? 'blinking' : ''}`}
      onMouseEnter={() => setShowDetails(true)}
      onMouseLeave={() => setShowDetails(false)}
      style={{ padding: '10px', border: '1px solid #777', borderRadius: '5px', background: 'white' }}
    >
      <div>{data.label}</div>
      {showDetails && (
        <div className="node-tooltip">
          <strong>Content:</strong> {data.content}<br />
          {data.metadata?.expected_result && <>
            <strong>Expected:</strong> {data.metadata.expected_result}<br />
           </>}
           {data.metadata?.ui_elements?.length > 0 && <>
            <strong>UI Elements:</strong> {data.metadata.ui_elements.join(', ')}<br />
           </>}
           {data.metadata?.inputs?.length > 0 && <>
            <strong>Inputs:</strong> {data.metadata.inputs.join(', ')}<br />
           </>}          
        </div>
      )}
    </div>
  );
};

const nodeTypes = { custom: CustomNode };

function TracerPage() {
  const { bugId } = useParams();
  const navigate = useNavigate();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [logs, setLogs] = useState([`[${new Date().toLocaleTimeString()}] Initializing Tracer for Bug ${bugId}...`]);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [needsGuidance, setNeedsGuidance] = useState(false);
  const [guidanceInput, setGuidanceInput] = useState('');

  // Load initial graph data
  useEffect(() => {
    const initialNodes = dummyTaskGraph.task_graph.nodes.map(node => ({
      ...node,
      data: { ...node.data, isCurrent: false } // Initialize isCurrent
    }));
    setNodes(initialNodes);
    setEdges(dummyTaskGraph.task_graph.edges);
    addLog('Task graph loaded.');
  }, [setNodes, setEdges, bugId]); // Added bugId dependency

  const addLog = (message) => {
    setLogs(prevLogs => [...prevLogs, `[${new Date().toLocaleTimeString()}] ${message}`]);
  };

  // Simulation Effect
  useEffect(() => {
    let timer;
    if (isRunning && !isPaused && currentStepIndex < simulationSteps.length) {
      const stepId = simulationSteps[currentStepIndex];
      
      // Update node highlighting
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          data: { ...node.data, isCurrent: node.id === stepId },
        }))
      );

      addLog(`Executing Step ${stepId}: ${dummyTaskGraph.task_graph.nodes.find(n=>n.id===stepId)?.data?.label || 'Unknown'}`);
      
      // Simulate getting stuck randomly for demo purposes
      if (Math.random() < 0.15 && currentStepIndex > 0) { // ~15% chance after first step
        addLog(`Agent needs guidance on step ${stepId}. Please provide input.`);
        setNeedsGuidance(true);
        setIsPaused(true); // Pause on needing guidance
      } else {
        // Proceed to next step after delay
        timer = setTimeout(() => {
          setCurrentStepIndex(prevIndex => prevIndex + 1);
        }, SIMULATION_DELAY);
      }

    } else if (currentStepIndex >= simulationSteps.length && isRunning) {
      addLog('Simulation complete. Bug Reproduced (Simulated).');
      setIsRunning(false);
      // Mark last node as finished (remove blinking)
       setNodes((nds) =>
        nds.map((node) => ({ ...node, data: { ...node.data, isCurrent: false }}))
       );
      // Navigate to results page after a short delay
      setTimeout(() => {
        navigate(`/tracer/${bugId}/results?reproduced=true`); // Pass result via query param for demo
      }, 1500);
    }

    // Cleanup timer on component unmount or when simulation stops/pauses
    return () => clearTimeout(timer);
  }, [isRunning, isPaused, currentStepIndex, setNodes, bugId, navigate]); // Added dependencies

  const handleToggleRun = () => {
    if (isRunning) {
      setIsPaused(!isPaused);
      addLog(isPaused ? 'Resuming simulation...' : 'Pausing simulation...');
    } else {
      setCurrentStepIndex(0); // Start from beginning
      setLogs([`[${new Date().toLocaleTimeString()}] Starting simulation for Bug ${bugId}...`]);
      setIsRunning(true);
      setIsPaused(false);
      setNeedsGuidance(false);
      addLog('Simulation started.');
    }
  };

  const handleProvideGuidance = () => {
    if (!guidanceInput) return;
    const stepId = simulationSteps[currentStepIndex];
    addLog(`User provided guidance for step ${stepId}: ${guidanceInput}`);
    setGuidanceInput('');
    setNeedsGuidance(false);
    setIsPaused(false); // Resume simulation after guidance
     // Immediately move to next step after guidance
     setCurrentStepIndex(prevIndex => prevIndex + 1);
  };

  const getCurrentStepInfo = () => {
    if (currentStepIndex < simulationSteps.length) {
      const currentId = simulationSteps[currentStepIndex];
      const node = dummyTaskGraph.task_graph.nodes.find(n => n.id === currentId);
      return node ? `Current Step (${currentId}): ${node.data.content}` : 'Starting...';
    } 
    return isRunning ? 'Finishing simulation...' : 'Simulation stopped.';
  };

  return (
    <div style={{ display: 'flex', height: '80vh', gap: '15px' }}>
      <div style={{ flex: 3, border: '1px solid #ccc', position: 'relative' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes} // Use custom node type
          fitView
        >
          <Controls />
          <MiniMap />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
         <div className="current-step-info">
           {getCurrentStepInfo()}
        </div>
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', border: '1px solid #ccc', padding: '10px' }}>
        <h3>CUA Simulation & Logs</h3>
        <div style={{ marginBottom: '15px' }}>
          <button onClick={handleToggleRun} disabled={needsGuidance && !isPaused}>
            {isRunning ? (isPaused ? 'Resume' : 'Pause') : 'Start CUA'}
          </button>
          <span style={{ marginLeft: '10px' }}>Status: {isRunning ? (isPaused ? 'Paused' : 'Running') : 'Stopped'}</span>
        </div>
        
        {needsGuidance && (
          <div className="guidance-box">
            <h4>Agent Needs Guidance</h4>
            <p>The agent is stuck on the current step. Please provide instructions:</p>
            <textarea 
              rows={3}
              value={guidanceInput}
              onChange={(e) => setGuidanceInput(e.target.value)}
              placeholder="e.g., Click the 'Submit' button instead of 'Save'"
              style={{ width: '95%', marginBottom: '5px' }}
            />
            <button onClick={handleProvideGuidance}>Provide Guidance & Resume</button>
          </div>
        )}

        <h4>Logs</h4>
        <div className="log-box">
          {logs.slice().reverse().map((log, index) => (
            <p key={index} style={{ margin: '2px 0', fontSize: '0.9em' }}>{log}</p>
          ))}
        </div>
      </div>
    </div>
  );
}

export default TracerPage; 