import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow';

import 'reactflow/dist/style.css';
import './DemoPlayerPage.css'; // Styles for this demo page

// Import Demo Data (Make sure this path is correct)
import { demoTaskGraphNodes as hardcodedNodes, demoTaskGraphEdges as hardcodedEdges, demoAgentLogs, demoBugId } from './demoData.js';

const DEMO_STEP_DELAY = 2000; // Adjusted for a slightly quicker demo if preferred
// const TARGET_DEMO_STEP_COUNT = 3; // Old: Play steps 1, 2, 3
// New: Play all steps from the hardcoded data
const TARGET_DEMO_STEP_COUNT = hardcodedNodes.length; // This should be 7 for the Twitter bug

// Custom Node Component (copied from TracerPage, ensure it uses data correctly)
const CustomNode = ({ data }) => {
  const [showDetails, setShowDetails] = useState(false);
  const { id, label, content, metadata, isCurrent } = data; // Removed isBlinking, category for simplicity if not used
  const MAX_TITLE_LENGTH = 40; // Adjusted for slightly more text if needed
  const conciseTitle = label && label.length > MAX_TITLE_LENGTH 
    ? label.substring(0, MAX_TITLE_LENGTH - 3) + "..." 
    : label;

  return (
    <div
      className={`custom-node ${isCurrent ? 'current' : ''} category-${data.category || 'default'}`}
      onMouseEnter={() => setShowDetails(true)}
      onMouseLeave={() => setShowDetails(false)}
    >
      <div className="node-label">Step {id}: {conciseTitle}</div>
      {showDetails && (
        <div className="node-tooltip">
          {label && <><string>Title:</string><div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', marginBottom: '5px' }}>{label}</div></>}
          {content && content !== label && <><hr style={{margin: '6px 0', borderColor: '#555'}} /><strong>Details:</strong><div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', marginBottom: '5px' }}>{content}</div></>}
          {((label || (content && content !== label)) && (metadata?.expected_result || metadata?.ui_elements?.length > 0 || metadata?.inputs?.length > 0)) &&
            <hr style={{margin: '6px 0', borderColor: '#555'}} />
          }
          {metadata?.expected_result && <><strong>Expected:</strong> {metadata.expected_result}<br /></>}
          {metadata?.ui_elements?.length > 0 && <><strong>UI Elements:</strong> {metadata.ui_elements.join(', ')}<br /></>}
          {metadata?.inputs?.length > 0 && <><strong>Inputs:</strong> {metadata.inputs.join(', ')}<br /></>}          
        </div>
      )}
    </div>
  );
};
const nodeTypes = { custom: CustomNode };

function DemoPlayerPage() {
  const navigate = useNavigate();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [_internalStepCounter, set_InternalStepCounter] = useState(-1); // -1: not started, 0-2: steps 1-3
  const [isRunning, setIsRunning] = useState(false);
  const [displayedLogs, setDisplayedLogs] = useState([]);
  const [currentStepInfoText, setCurrentStepInfoText] = useState("Demo ready to start.");
  const demoTimeoutRef = useRef(null);

  // Initial setup of graph
  useEffect(() => {
    const initialFlowNodes = hardcodedNodes.map((node, idx) => ({
      ...node,
      data: { ...node.data, isCurrent: idx === 0 }, // Highlight first node by default
    }));
    setNodes(initialFlowNodes);
    const styledFlowEdges = hardcodedEdges.map(edge => ({ ...edge, markerEnd: { type: MarkerType.ArrowClosed, width: 15, height: 15, color: '#777' }}));
    setEdges(styledFlowEdges);
    setDisplayedLogs([`[DEMO] Ready. Click "Start Demo" to play sequence for bug: ${demoBugId}.`]);
    if(hardcodedNodes.length > 0 && hardcodedNodes[0].data){
         setCurrentStepInfoText(`Step 1: ${hardcodedNodes[0].data.label}`);
    }
    return () => clearTimeout(demoTimeoutRef.current);
  }, [setNodes, setEdges]);

  // Main demo logic effect
  useEffect(() => {
    clearTimeout(demoTimeoutRef.current); // Clear previous timeout before setting a new one or finishing

    if (!isRunning || _internalStepCounter < 0 || _internalStepCounter >= TARGET_DEMO_STEP_COUNT) {
      // If not running, or counter is out of typical bounds, do nothing further in this effect.
      if (_internalStepCounter >= TARGET_DEMO_STEP_COUNT && isRunning) { // Edge case: if counter somehow went too far but was running
         setIsRunning(false); // Ensure it stops
      }
      return;
    }

    const currentProcessingNode = hardcodedNodes[_internalStepCounter];
    if (!currentProcessingNode) return; // Should not happen if counter is managed well
    const currentDemoNodeId = currentProcessingNode.id;

    // 1. Update Node Highlighting
    setNodes((prevNodes) => prevNodes.map((node) => ({ ...node, data: { ...node.data, isCurrent: node.id === currentDemoNodeId }})));

    // 2. Update Current Step Info Bar
    setCurrentStepInfoText(`Step ${currentDemoNodeId}: ${currentProcessingNode.data.label}`);

    // 3. Aggregate and Set Logs
    let logsToShow = [];
    for (let i = 0; i <= _internalStepCounter; i++) {
      if (demoAgentLogs[i]) { // Check if the log block exists
        logsToShow.push(demoAgentLogs[i]);
      }
    }
    const executionMessage = `[${new Date().toLocaleTimeString()}] [DEMO] Displaying logs for: Step ${currentDemoNodeId} - ${currentProcessingNode.data.label}`;
    setDisplayedLogs([...logsToShow.map(logBlock => `[DEMO LOG BLOCK]\n${logBlock}`), executionMessage]); // Prefix each block for clarity

    // 4. Schedule Next Step or Navigate
    if (_internalStepCounter < TARGET_DEMO_STEP_COUNT - 1) { // If there are more steps to play in the 3-step demo
      demoTimeoutRef.current = setTimeout(() => {
        set_InternalStepCounter(prev => prev + 1);
      }, DEMO_STEP_DELAY);
    } else { // This was the last step of the 3-step demo (i.e. _internalStepCounter === TARGET_DEMO_STEP_COUNT - 1)
      demoTimeoutRef.current = setTimeout(() => {
        setIsRunning(false);
        const finalLogsForDisplay = demoAgentLogs.slice(0, TARGET_DEMO_STEP_COUNT); // Get all relevant step logs
        const finalVerificationLog = demoAgentLogs.length > TARGET_DEMO_STEP_COUNT ? demoAgentLogs[TARGET_DEMO_STEP_COUNT] : "[DEMO] All steps shown.";
        const completionMessage = `[${new Date().toLocaleTimeString()}] [DEMO] All ${TARGET_DEMO_STEP_COUNT} steps shown. Bug Reproduced! Navigating...`;
        setDisplayedLogs([
            ...finalLogsForDisplay.map(logBlock => `[DEMO LOG BLOCK]\n${logBlock}`),
            `[DEMO LOG BLOCK]\n${finalVerificationLog}`,
            completionMessage
        ]);
        setCurrentStepInfoText("Demo complete. Navigating...");
        
        setTimeout(() => { // Nested timeout for navigation after final log display
            navigate(`/tracer/${demoBugId}/results?reproduced=true&demo=true`, { 
              state: { demoLogs: demoAgentLogs, bugTitle: "X/Twitter Share Link Leads to NXDOMAIN (Demo)" } // Pass the structured logs
            });
        }, 1500); // Increased delay slightly before navigation
      }, DEMO_STEP_DELAY);
    }

    return () => clearTimeout(demoTimeoutRef.current);
  }, [_internalStepCounter, isRunning, setNodes, navigate]);

  const handleStartStopDemo = () => {
    if (isRunning) {
      setIsRunning(false);
      clearTimeout(demoTimeoutRef.current);
      setDisplayedLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] [DEMO] Stopped by user.`]);
      setCurrentStepInfoText("Demo stopped by user.");
    } else {
      set_InternalStepCounter(0); // Start from the first step (index 0)
      setDisplayedLogs([`[${new Date().toLocaleTimeString()}] [DEMO] Starting sequence for bug: ${demoBugId}...`]);
      setIsRunning(true);
    }
  };
  
  return (
    <div className="demo-player-container">
      <div className="reactflow-panel">
        <div className="reactflow-wrapper">
          <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} nodeTypes={nodeTypes} fitView fitViewOptions={{ padding: 0.1 }}>
            <Controls />
            <MiniMap />
            <Background variant="dots" gap={12} size={1} />
          </ReactFlow>
        </div>
        <div className="current-step-info-demo">
          {currentStepInfoText}
        </div>
      </div>
      <div className="simulation-panel">
        <h3>DEMO: Twitter/X Share Bug</h3>
        <div style={{ marginBottom: '15px' }}>
          <button onClick={handleStartStopDemo}>
            {isRunning ? 'Stop Demo' : 'Start Demo'}
          </button>
          <span className="status-text">
            Status: {isRunning ? `Running (Step ${_internalStepCounter + 1}/${TARGET_DEMO_STEP_COUNT})` : (_internalStepCounter >= TARGET_DEMO_STEP_COUNT -1 && _internalStepCounter !== -1 ? 'Completed' : 'Stopped')}
          </span>
        </div>
        <h4>Logs</h4>
        <div className="log-box">
          {displayedLogs.slice().reverse().map((log, index) => (<p key={index} style={{whiteSpace: 'pre-wrap'}}>{log}</p>))}
        </div>
        <button onClick={() => navigate(`/tracer/${demoBugId}/results?reproduced=true&demo=true`, { state: { demoLogs: demoAgentLogs, bugTitle: "X/Twitter Share Link Leads to NXDOMAIN (Demo)" }})} style={{ marginTop: '15px'}} disabled={isRunning}>
            Go to Results Page (Manual)
        </button>
      </div>
    </div>
  );
}

export default DemoPlayerPage; 