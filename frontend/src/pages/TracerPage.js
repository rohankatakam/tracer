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

// Static public demo data matching the TaskGraphGenerator shape.
const dummyTaskGraph = {
  name: "academybugs_currency_freeze_01",
  description: "Illustrative task graph for a public AcademyBugs report",
  environment: { application: "AcademyBugs.com", browser: "Firefox" },
  task_graph: {
    nodes: [
      {
        id: "1",
        type: "custom",
        position: { x: 50, y: 50 },
        data: {
          label: "Step 1: Open demo site",
          content: "Navigate to the public AcademyBugs Find Bugs page.",
          metadata: { image_refs: [], ui_elements: ['Browser address bar'], inputs: ['https://academybugs.com/find-bugs/'], expected_result: "The public bug gallery is visible" }
        }
      },
      {
        id: "2",
        type: "custom",
        position: { x: 50, y: 180 },
        data: {
          label: "Step 2: Open a product",
          content: "Select the first available product and open its detail page.",
          metadata: { image_refs: [], ui_elements: ['Product card', 'Product link'], inputs: [], expected_result: "A product detail page is visible" }
        }
      },
      {
        id: "3",
        type: "custom",
        position: { x: 50, y: 310 },
        data: {
          label: "Step 3: Find currency control",
          content: "Locate and open the currency selection control.",
          metadata: { image_refs: [], ui_elements: ['Currency selector'], inputs: [], expected_result: "Currency options are visible" }
        }
      },
      {
        id: "4",
        type: "custom",
        position: { x: 300, y: 440 },
        data: {
          label: "Step 4: Change currency",
          content: "Choose a currency different from the currently selected value.",
          metadata: { image_refs: [], ui_elements: ['Currency option'], inputs: ['A different listed currency'], expected_result: "The selection event is submitted" }
        }
      },
      {
        id: "5",
        type: "custom",
        position: { x: 300, y: 570 },
        data: {
          label: "Step 5: Observe response",
          content: "Observe whether the page responds to input or remains in a loading state.",
          metadata: { image_refs: [], ui_elements: ['Page controls', 'Loading indicator'], inputs: [], expected_result: "Responsiveness can be assessed" }
        }
      },
      {
        id: "6",
        type: "custom",
        position: { x: 550, y: 700 },
        data: {
          label: "Step 6: Capture evidence",
          content: "Capture the final browser state and mark the trace for human review.",
          metadata: { image_refs: [], ui_elements: ['Browser viewport'], inputs: [], expected_result: "A reviewer has a screenshot and structured trace" }
        }
      },
    ],
    edges: [
      { id: 'e1-2', source: '1', target: '2', animated: true },
      { id: 'e2-3', source: '2', target: '3', animated: true },
      { id: 'e3-4', source: '3', target: '4', animated: true },
      { id: 'e4-5', source: '4', target: '5', animated: true },
      { id: 'e5-6', source: '5', target: '6', animated: true },
    ]
  },
  verification_steps: ["Review the trace and final browser state for responsiveness"],
  missing_information: ["A live run is required before determining whether the report reproduces"]
};

// --- Dummy Simulation Logic ---
const simulationSteps = dummyTaskGraph.task_graph.nodes.map(n => n.id);
const SIMULATION_DELAY = 1500;
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
      
      timer = setTimeout(() => {
        setCurrentStepIndex(prevIndex => prevIndex + 1);
      }, SIMULATION_DELAY);

    } else if (currentStepIndex >= simulationSteps.length && isRunning) {
      addLog('Simulation complete. Evidence is ready for human review.');
      setIsRunning(false);
      // Mark last node as finished (remove blinking)
       setNodes((nds) =>
        nds.map((node) => ({ ...node, data: { ...node.data, isCurrent: false }}))
       );
      // Navigate to results page after a short delay
      setTimeout(() => {
        navigate(`/tracer/${bugId}/results?simulation=complete`);
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
        <h3>Static Flow Simulation</h3>
        <div style={{ marginBottom: '15px' }}>
          <button onClick={handleToggleRun} disabled={needsGuidance && !isPaused}>
            {isRunning ? (isPaused ? 'Resume' : 'Pause') : 'Start Simulation'}
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
