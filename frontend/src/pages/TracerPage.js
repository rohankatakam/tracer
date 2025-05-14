import React, { useState, useEffect, useCallback, useRef } from 'react';
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

// Import Demo Data
import { demoBugId, demoTaskGraphNodes, demoTaskGraphEdges, demoAgentLogs } from './demoData.js';

// --- Constants for Demo Mode ---
const DEMO_STEP_DELAY = 2000; // Shortened for quicker testing, adjust as needed

// --- Dummy Task Graph Data ---
// Matches the structure from TaskGraphGenerator
// const dummyTaskGraph = { ... } // REMOVE THIS ENTIRE DUMMY DATA OBJECT
// --- End Dummy Task Graph Data ---

// --- Dummy Simulation Logic ---
// const simulationSteps = dummyTaskGraph.task_graph.nodes.map(n => n.id); // REMOVE THIS
// const SIMULATION_DELAY = 2500; // Original, can be removed if non-demo uses DEMO_STEP_DELAY or has its own

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
  
  const [logs, setLogs] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [needsGuidance, setNeedsGuidance] = useState(false);
  const [guidanceInput, setGuidanceInput] = useState('');

  const isDemoMode = bugId === demoBugId;
  const demoTimeoutRef = useRef(null); // To store timeout ID for clearing

  const addLog = useCallback((message) => {
    setLogs(prevLogs => [...prevLogs, `[${new Date().toLocaleTimeString()}] ${message}`]);
  }, []);

  // Effect to load data (API or Demo)
  useEffect(() => {
    if (isDemoMode) {
      setLogs([`[${new Date().toLocaleTimeString()}] Initializing DEMO for Bug ${bugId}...`]);
      const initialDemoNodes = demoTaskGraphNodes.map((node, idx) => ({
        ...node,
        data: { ...node.data, isCurrent: idx === 0, isBlinking: false },
      }));
      setNodes(initialDemoNodes);
      setEdges(demoTaskGraphEdges.map(edge => ({ ...edge, markerEnd: { type: MarkerType.ArrowClosed, width: 15, height: 15, color: '#777' }})));
      setIsLoading(false);
      setCurrentStepIndex(0); // Explicitly set to 0 for demo start
    } else {
      // Original API fetching logic
      const fetchTaskGraph = async () => {
        setIsLoading(true);
        setError(null);
        setLogs([`[${new Date().toLocaleTimeString()}] Initializing Tracer for Bug ${bugId}...`]);
        addLog(`Fetching task graph for Bug ${bugId}...`);
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
          setTaskGraphData(null);
        } finally {
          setIsLoading(false);
        }
      };
      if (bugId) fetchTaskGraph();
    }
    // Cleanup timeout when component unmounts or bugId/isDemoMode changes
    return () => clearTimeout(demoTimeoutRef.current);
  }, [bugId, isDemoMode, setNodes, setEdges, addLog]);

  // Effect to update ReactFlow nodes and edges when taskGraphData is loaded (for non-demo)
  useEffect(() => {
    if (!isDemoMode && taskGraphData && taskGraphData.task_graph && taskGraphData.task_graph.nodes) {
      const initialNodes = taskGraphData.task_graph.nodes.map((apiNode, index) => ({
        id: apiNode.id,
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
      const styledEdges = (taskGraphData.task_graph.edges || []).map(edge => ({
        ...edge,
        style: { stroke: '#777', strokeWidth: 1.5, strokeDasharray: '5 5' },
        animated: false,
        markerEnd: { type: MarkerType.ArrowClosed, width: 15, height: 15, color: '#777' },
      }));
      setEdges(styledEdges);
    } else if (!isDemoMode && !taskGraphData && !isLoading) {
      setNodes([]);
      setEdges([]);
    }
  }, [taskGraphData, setNodes, setEdges, isDemoMode, isLoading]);
  
  // Effect to handle demo step progression & UI updates based on currentStepIndex
  useEffect(() => {
    if (isDemoMode && isRunning && currentStepIndex >= 0) {
      const demoNodes = demoTaskGraphNodes;
      const targetDemoStepCount = 3; // Steps 0, 1, 2

      // Define separatorIndices here so it's available for both progression and completion logic
      const separatorIndices = demoAgentLogs.reduce((acc, log, idx) => (log === "---" ? [...acc, idx] : acc), []);

      if (currentStepIndex < targetDemoStepCount) {
        const currentProcessingNode = demoNodes[currentStepIndex];
        const currentDemoNodeId = currentProcessingNode.id;

        // Highlight current node
        setNodes((nds) => nds.map((node) => ({ ...node, data: { ...node.data, isCurrent: node.id === currentDemoNodeId }})));
        
        // Aggregate and set logs
        let logsToShow = [];
        if (currentStepIndex === 0) {
          logsToShow = demoAgentLogs.slice(0, separatorIndices.length > 0 ? separatorIndices[0] : demoAgentLogs.length);
        } else {
          const endIndex = currentStepIndex < separatorIndices.length ? separatorIndices[currentStepIndex] : demoAgentLogs.length;
          logsToShow = demoAgentLogs.slice(0, endIndex);
        }
        const executionMessage = `[${new Date().toLocaleTimeString()}] [DEMO] Now on: Step ${currentDemoNodeId} - ${currentProcessingNode.data.label}`;
        setLogs([...logsToShow.map(log => log.startsWith("---") ? log : `[DEMO] ${log}`), executionMessage]);

        // Schedule next step
        demoTimeoutRef.current = setTimeout(() => {
          setCurrentStepIndex(prev => prev + 1);
        }, DEMO_STEP_DELAY);

      } else { // Demo sequence finished
        setIsRunning(false); // Stop the demo
        let finalLogEndIndex = demoAgentLogs.length;
        if (targetDemoStepCount > 0) {
            // We want logs up to the end of the *last processed step*.
            // If targetDemoStepCount is 3 (steps 0, 1, 2), the last processed step is index 2.
            // We need the separator *after* step 2 logs, which is separatorIndices[2].
            // If targetDemoStepCount-1 is a valid index for separatorIndices:
            if (separatorIndices[targetDemoStepCount - 1] !== undefined) {
                finalLogEndIndex = separatorIndices[targetDemoStepCount - 1];
            } else if (targetDemoStepCount > separatorIndices.length) {
                // If target steps exceed available separators (e.g. last step has no trailing ---)
                finalLogEndIndex = demoAgentLogs.length; // Show all logs
            }
        } else {
            finalLogEndIndex = 0; // No logs if no steps were to be shown
        }
        const finalLogs = demoAgentLogs.slice(0, finalLogEndIndex);

        const completionMessage = `[${new Date().toLocaleTimeString()}] [DEMO] Sequence complete. Navigating...`;
        setLogs([...finalLogs.map(log => log.startsWith("---") ? log : `[DEMO] ${log}`), completionMessage]);
        
        if (demoNodes.length > 0 && targetDemoStepCount > 0) {
          const lastNodeId = demoNodes[targetDemoStepCount - 1].id;
          setNodes((nds) => nds.map(node => ({...node, data: {...node.data, isCurrent: node.id === lastNodeId }})));
        }

        setTimeout(() => {
          navigate(`/tracer/${bugId}/results?reproduced=true&demo=true`, { state: { demoLogs: demoAgentLogs, bugTitle: "X/Twitter Share Link Leads to NXDOMAIN (Demo)" } });
        }, 1000); // Shorter delay before navigation
      }
    } else if (!isRunning && demoTimeoutRef.current) {
        clearTimeout(demoTimeoutRef.current); // Clear timeout if demo is stopped manually
    }

    // Non-demo simulation (simplified, needs isPaused and needsGuidance if full functionality is restored)
    if (!isDemoMode && isRunning && !isPaused) {
      if (taskGraphData && taskGraphData.task_graph && taskGraphData.task_graph.nodes && currentStepIndex < taskGraphData.task_graph.nodes.length) {
        const simulationSteps = taskGraphData.task_graph.nodes.map(n => n.id);
        const stepId = simulationSteps[currentStepIndex];
        setNodes((nds) => nds.map((node) => ({ ...node, data: { ...node.data, isCurrent: node.id === stepId, isBlinking: node.id === stepId && needsGuidance }})));
        const reactFlowNode = nodes.find(n => n.id === stepId);
        const newLogEntry = `[${new Date().toLocaleTimeString()}] Executing Step ${stepId}: ${reactFlowNode?.data?.label || 'Unknown Step'}`;
        setLogs(prev => [...prev, newLogEntry]);
        demoTimeoutRef.current = setTimeout(() => setCurrentStepIndex(prevIndex => prevIndex + 1), DEMO_STEP_DELAY);
      } else if (taskGraphData?.task_graph?.nodes && currentStepIndex >= taskGraphData.task_graph.nodes.length) {
        setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Simulation complete.`]);
        setIsRunning(false);
        setNodes((nds) => nds.map((node) => ({ ...node, data: { ...node.data, isCurrent: false, isBlinking: false }})));
        navigate(`/tracer/${bugId}/results?reproduced=true`);
      }
    }

    return () => clearTimeout(demoTimeoutRef.current);
  }, [isRunning, currentStepIndex, isDemoMode, bugId, navigate, setNodes, nodes, taskGraphData, isPaused, needsGuidance]); // Added nodes, taskGraphData, isPaused, needsGuidance for non-demo path

  const handleToggleRun = () => {
    if (isRunning) {
      setIsRunning(false);
      clearTimeout(demoTimeoutRef.current); // Clear any pending demo step
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${isDemoMode ? 'DEMO Stopped.' : 'Simulation Paused/Stopped.'}`]);
    } else {
      setCurrentStepIndex(0); // Reset to first step
      setLogs([`[${new Date().toLocaleTimeString()}] ${isDemoMode ? 'Starting DEMO...' : 'Starting CUA Simulation...'}`]);
      setIsRunning(true); 
      // For demo, the useEffect on isRunning & currentStepIndex will now pick up and start the sequence.
      // For non-demo, it also relies on this combination.
    }
  };

  const handleProvideGuidance = () => {
    if (!guidanceInput || isDemoMode) return;
    if (!taskGraphData || !taskGraphData.task_graph || !taskGraphData.task_graph.nodes) return; 
    const simulationSteps = taskGraphData.task_graph.nodes.map(n => n.id); 
    const stepId = simulationSteps[currentStepIndex];
    addLog(`User provided guidance for step ${stepId}: ${guidanceInput}`);
    setGuidanceInput('');
    setNeedsGuidance(false);
    setIsPaused(false); 
    setCurrentStepIndex(prevIndex => prevIndex + 1);
  };

  // getCurrentStepInfo needs to be aware of demo mode
  const getCurrentStepInfo = () => {
    if (isLoading && !isDemoMode) return 'Loading task graph...'; // isLoading is primarily for API calls
    if (!isDemoMode && error) return `Error: ${error}`;
    
    if (isDemoMode) {
      if (currentStepIndex >= 0 && currentStepIndex < demoTaskGraphNodes.length) {
        const demoNode = demoTaskGraphNodes[currentStepIndex];
        if (demoNode && demoNode.data) {
          const stepId = demoNode.data.id;
          const content = demoNode.data.content || demoNode.data.label || 'No content for this demo step.';
          return `Current Step (${stepId}): ${content}`;
        }
      }
      if (isRunning) return 'Finishing demo...';
      return 'Demo stopped or not started.';
    }

    // Non-demo mode logic
    const currentNodesSource = taskGraphData?.task_graph?.nodes || [];
    if (!currentNodesSource || currentNodesSource.length === 0) return 'No task graph data.';

    if (currentStepIndex >= 0 && currentStepIndex < currentNodesSource.length) {
      const currentNode = currentNodesSource[currentStepIndex];
      if (currentNode && currentNode.data) {
        const stepId = currentNode.id;
        const content = currentNode.data.content || currentNode.data.label || 'No content for this step.';
        return `Current Step (${stepId}): ${content}`;
      }
    } 
    if (isRunning) return 'Finishing simulation...';
    return 'Simulation stopped.';
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
  
  if (!isDemoMode && (!taskGraphData || !taskGraphData.task_graph || !taskGraphData.task_graph.nodes || taskGraphData.task_graph.nodes.length === 0)) {
    // Adjusted this condition to not block demo mode if taskGraphData isn't fully set up in the same way
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
            style={{ width: '100%', height: '100%' }}
          >
            <Controls />
            <MiniMap />
            <Background variant="dots" gap={12} size={1} />
          </ReactFlow>
        </div>
         <div className={`current-step-info ${isDemoMode ? '' : (needsGuidance ? 'needs-guidance' : '')}`}>
           {getCurrentStepInfo()}
        </div>
      </div>
      <div className="simulation-panel">
        <h3>{isDemoMode ? 'DEMO Simulation & Logs' : 'CUA Simulation & Logs'}</h3>
        <div style={{ marginBottom: '15px' }}>
          <button onClick={handleToggleRun} disabled={!isDemoMode && isRunning && needsGuidance && !isPaused } >
            {isRunning ? (isDemoMode ? 'Stop Demo' : (isPaused ? 'Resume' : 'Pause')) : (isDemoMode ? 'Start Demo' : 'Start CUA')}
          </button>
          <span className="status-text">
            Status: {isRunning ? 'Running' : 'Stopped'} {isDemoMode && isRunning && currentStepIndex < (isDemoMode ? demoTaskGraphNodes.length : (taskGraphData?.task_graph?.nodes?.length || 0)) ? `(Step ${currentStepIndex +1})` : ''}
          </span>
        </div>
        
        {!isDemoMode && needsGuidance && (
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
        
        <button 
            onClick={() => navigate(`/tracer/${bugId}/results?reproduced=${isRunning && !isDemoMode ? 'false' : 'true'}${isDemoMode ? '&demo=true' : ''}`, isDemoMode ? { state: { demoLogs: demoAgentLogs, bugTitle: "X/Twitter Share Link Leads to NXDOMAIN (Demo)" } } : {} )} 
            style={{ marginTop: '15px'}} 
            disabled={isRunning && !isPaused && !isDemoMode}
        >
            Go to Results Page
        </button>
      </div>
    </div>
  );
}

export default TracerPage; 