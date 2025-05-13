import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow';

import 'reactflow/dist/style.css';
import './TracerPage.css'; // Specific styles for this page

// --- Dummy Task Graph Data ---
// Matches the structure from TaskGraphGenerator
// const dummyTaskGraph = { ... } // REMOVE THIS ENTIRE DUMMY DATA OBJECT
// --- End Dummy Task Graph Data ---

// --- Dummy Simulation Logic ---
// const simulationSteps = dummyTaskGraph.task_graph.nodes.map(n => n.id); // REMOVE THIS
const SIMULATION_DELAY = 2500; // ms between steps
// --- End Dummy Simulation Logic ---

// Custom Node for potential styling/interactions
const CustomNode = ({ data }) => {
  const [showDetails, setShowDetails] = useState(false);

  // Destructure all necessary fields from data for clarity
  const { id, label, content, metadata, isCurrent, isBlinking, category } = data;

  // Create a concise version of the label for display in the node
  const MAX_TITLE_LENGTH = 35; // Adjust as needed for visual balance
  const conciseTitle = label && label.length > MAX_TITLE_LENGTH 
    ? label.substring(0, MAX_TITLE_LENGTH - 3) + "..." 
    : label;

  return (
    <div
      className={`custom-node ${isCurrent ? 'current' : ''} ${isBlinking ? 'blinking' : ''} category-${category || 'default'}`}
      onMouseEnter={() => setShowDetails(true)}
      onMouseLeave={() => setShowDetails(false)}
    >
      <div className="node-label">Step {id}: {conciseTitle}</div>
      {/* The detailed node-content is removed from the main node body to keep it concise */}
      
      {showDetails && (
        <div className="node-tooltip">
          {label && 
            <>
              <strong>Title:</strong>
              <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', marginBottom: '5px' }}>{label}</div> {/* Full original label */}
            </>
          }
          {/* Show content separately only if it exists and is different from the main label */}
          {content && content !== label && 
            <>
              <hr style={{margin: '6px 0', borderColor: '#555'}} />
              <strong>Details:</strong>
              <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', marginBottom: '5px' }}>{content}</div>
            </>
          }
          
          {/* Consistently add a separator if there was a title or content before metadata */}
          {((label || (content && content !== label)) && (metadata?.expected_result || metadata?.ui_elements?.length > 0 || metadata?.inputs?.length > 0)) &&
            <hr style={{margin: '6px 0', borderColor: '#555'}} />
          }

          {metadata?.expected_result && <>
            <strong>Expected:</strong> {metadata.expected_result}<br />
           </>}
           {metadata?.ui_elements?.length > 0 && <>
            <strong>UI Elements:</strong> {metadata.ui_elements.join(', ')}<br />
           </>}
           {metadata?.inputs?.length > 0 && <>
            <strong>Inputs:</strong> {metadata.inputs.join(', ')}<br />
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
  
  // New state variables for fetching data
  const [taskGraphData, setTaskGraphData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [logs, setLogs] = useState([`[${new Date().toLocaleTimeString()}] Initializing Tracer for Bug ${bugId}...`]);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [needsGuidance, setNeedsGuidance] = useState(false);
  const [guidanceInput, setGuidanceInput] = useState('');

  // Load initial graph data from API
  useEffect(() => {
    const fetchTaskGraph = async () => {
      setIsLoading(true);
      setError(null);
      setLogs(prevLogs => [...prevLogs, `[${new Date().toLocaleTimeString()}] Fetching task graph for Bug ${bugId}...`]);
      try {
        const response = await fetch(`http://localhost:5001/api/bugs/${bugId}/task_graph`, {
          method: 'GET',
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Expires': '0',
          },
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.description || `HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setTaskGraphData(data);
        addLog('Task graph loaded successfully from API.');
      } catch (e) {
        setError(e.message);
        addLog(`Error fetching task graph: ${e.message}`);
        setTaskGraphData(null); // Clear any partial data
      } finally {
        setIsLoading(false);
      }
    };

    if (bugId) {
      fetchTaskGraph();
    }
  }, [bugId]); // Removed setNodes, setEdges from dependencies, addLog is stable

  // Effect to update ReactFlow nodes and edges when taskGraphData is loaded/changed
  useEffect(() => {
    if (taskGraphData && taskGraphData.task_graph && taskGraphData.task_graph.nodes) {
      // Map API node structure to ReactFlow node structure
      const initialNodes = taskGraphData.task_graph.nodes.map((apiNode, index) => ({
        id: apiNode.id,
        // Fallback to a vertical layout if no position is provided by the API
        // Adjusted y-spacing to 100px to give nodes a bit more breathing room vertically
        position: apiNode.position || { x: 100, y: index * 100 }, 
        type: 'custom',
        data: {
          label: apiNode.data?.label || apiNode.content || `Step ${apiNode.id}`, 
          content: apiNode.content,
          metadata: apiNode.metadata || {},
          isCurrent: apiNode.id === '1' || (index === 0 && !taskGraphData.task_graph.nodes.find(n => n.id === '1')),
          isBlinking: false, 
          category: apiNode.data?.category || 'default',
          id: apiNode.id
        }
      }));
      setNodes(initialNodes);
      
      // Style edges to be dashed with arrowheads
      const styledEdges = (taskGraphData.task_graph.edges || []).map(edge => ({
        ...edge,
        style: { stroke: '#777', strokeWidth: 1.5, strokeDasharray: '5 5' }, // Adjusted dash array slightly
        animated: false,
        markerEnd: { 
          type: MarkerType.ArrowClosed,
          width: 15, // Size of the arrowhead
          height: 15,
          color: '#777', // Color of the arrowhead
        },
      }));
      setEdges(styledEdges);
    } else {
      // Clear nodes and edges if data is null (e.g., due to an error)
      setNodes([]);
      setEdges([]);
    }
  }, [taskGraphData, setNodes, setEdges]);

  const addLog = (message) => {
    setLogs(prevLogs => [...prevLogs, `[${new Date().toLocaleTimeString()}] ${message}`]);
  };

  // Simulation Effect
  useEffect(() => {
    let timer;
    // Ensure taskGraphData and its properties are loaded before trying to access them
    if (isRunning && !isPaused && taskGraphData && taskGraphData.task_graph && taskGraphData.task_graph.nodes && currentStepIndex < taskGraphData.task_graph.nodes.length) {
      const simulationSteps = taskGraphData.task_graph.nodes.map(n => n.id); // Derive simulationSteps here
      const stepId = simulationSteps[currentStepIndex];
      
      // Update node highlighting
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          data: { 
            ...node.data, 
            isCurrent: node.id === stepId, 
            isBlinking: node.id === stepId && needsGuidance
          },
        }))
      );

      // Find the *ReactFlow node* from state to get the label/content for logging
      const reactFlowNode = nodes.find(n => n.id === stepId);
      addLog(`Executing Step ${stepId}: ${reactFlowNode?.data?.label || 'Unknown Step'}`);
      
      // Simulate getting stuck randomly for demo purposes
      if (Math.random() < 0.15 && currentStepIndex > 0) { // ~15% chance after first step
        addLog(`Agent needs guidance on step ${stepId}. Please provide input.`);
        setNeedsGuidance(true);
        setIsPaused(true); // Pause on needing guidance
        // Update the current node to set isBlinking to true
        setNodes((nds) => 
          nds.map((n) => 
            n.id === stepId ? { ...n, data: { ...n.data, isBlinking: true, isCurrent: true } } : n
          )
        );
      } else {
        // Proceed to next step after delay
        timer = setTimeout(() => {
          setCurrentStepIndex(prevIndex => prevIndex + 1);
        }, SIMULATION_DELAY);
      }

    } else if (taskGraphData && taskGraphData.task_graph && taskGraphData.task_graph.nodes && currentStepIndex >= taskGraphData.task_graph.nodes.length && isRunning) {
      addLog('Simulation complete. Bug Reproduced (Simulated).');
      setIsRunning(false);
      // Mark last node as finished (remove blinking and current)
       setNodes((nds) =>
        nds.map((node) => ({ ...node, data: { ...node.data, isCurrent: false, isBlinking: false }}))
       );
      // Navigate to results page after a short delay
      addLog(`Preparing to navigate to results for bug ${bugId}`);
      setTimeout(() => {
        navigate(`/tracer/${bugId}/results?reproduced=true`); // Pass result via query param for demo
      }, 1500);
    }

    // Cleanup timer on component unmount or when simulation stops/pauses
    return () => clearTimeout(timer);
  }, [isRunning, isPaused, currentStepIndex, setNodes, bugId, navigate, taskGraphData, nodes, needsGuidance]); // Added needsGuidance

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
    if (!taskGraphData || !taskGraphData.task_graph || !taskGraphData.task_graph.nodes) return; // Guard
    const simulationSteps = taskGraphData.task_graph.nodes.map(n => n.id); // Derive simulationSteps here
    const stepId = simulationSteps[currentStepIndex];
    addLog(`User provided guidance for step ${stepId}: ${guidanceInput}`);
    setGuidanceInput('');
    setNeedsGuidance(false);
    setIsPaused(false); // Resume simulation after guidance
     // Immediately move to next step after guidance
     setCurrentStepIndex(prevIndex => prevIndex + 1);
  };

  const getCurrentStepInfo = () => {
    if (isLoading) return 'Loading task graph...';
    if (error) return `Error: ${error}`;
    // Use the 'nodes' state variable which holds the ReactFlow nodes
    if (!nodes || nodes.length === 0) return 'No task graph data available.'; 

    // Derive simulationSteps from the ReactFlow 'nodes' state if needed, or keep using taskGraphData if preferred
    // Let's derive from taskGraphData as it's the source of truth for steps
    if (!taskGraphData || !taskGraphData.task_graph || !taskGraphData.task_graph.nodes) return 'Task graph structure missing.';
    const simulationSteps = taskGraphData.task_graph.nodes.map(n => n.id); 
    
    if (currentStepIndex < simulationSteps.length) {
      const currentId = simulationSteps[currentStepIndex];
      // Find the corresponding ReactFlow node from the 'nodes' state
      const reactFlowNode = nodes.find(n => n.id === currentId);
      // Access the content from the node's data property
      return reactFlowNode ? `Current Step (${currentId}): ${reactFlowNode.data.content}` : 'Starting...';
    } 
    return isRunning ? 'Finishing simulation...' : 'Simulation stopped.';
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <h2>Loading Task Graph for Bug ID: {bugId}...</h2>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '80vh', color: 'red' }}>
        <h2>Error loading Task Graph for Bug ID: {bugId}</h2>
        <p>{error}</p>
        <button onClick={() => navigate('/bugs')}>Go back to Bug List</button>
      </div>
    );
  }
  
  if (!taskGraphData || !taskGraphData.task_graph || !taskGraphData.task_graph.nodes || taskGraphData.task_graph.nodes.length === 0) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <h2>No Task Graph Data Available for Bug ID: {bugId}</h2>
        <p>The API might have returned an empty graph or there was an issue processing it.</p>
        <button onClick={() => navigate('/bugs')}>Go back to Bug List</button>
      </div>
    );
  }

  return (
    <div className="tracer-page-container">
      <div className="reactflow-panel">
        <div className="reactflow-wrapper">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.1 }}
            style={{ width: '100%', height: '100%' }} // Make ReactFlow fill this container
          >
            <Controls />
            <MiniMap />
            <Background variant="dots" gap={12} size={1} />
          </ReactFlow>
        </div>
         <div className={`current-step-info ${needsGuidance ? 'needs-guidance' : ''}`}>
           {getCurrentStepInfo()}
        </div>
      </div>
      <div className="simulation-panel">
        <h3>CUA Simulation & Logs</h3>
        <div style={{ marginBottom: '15px' }}>
          <button onClick={handleToggleRun} disabled={needsGuidance && !isPaused}>
            {isRunning ? (isPaused ? 'Resume' : 'Pause') : 'Start CUA'}
          </button>
          <span className="status-text">
            Status: {isRunning ? (isPaused ? 'Paused' : 'Running') : 'Stopped'}
          </span>
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
        
        {/* Add a manual button to go to results, visible if graph is loaded */}
        {taskGraphData && taskGraphData.task_graph && (
            <button 
                onClick={() => navigate(`/tracer/${bugId}/results?reproduced=false&manual_nav=true`)} 
                style={{ marginTop: '15px'}} 
                disabled={isRunning && !isPaused} // Disable if simulation is actively running and not paused
            >
                Go to Results Page
            </button>
        )}
      </div>
    </div>
  );
}

export default TracerPage; 