export const demoBugId = 'academybugs_twitter_share_nxdomain_01_demo';

export const demoTaskGraphNodes = [
  {
    id: "1",
    type: "custom",
    data: {
      id: "1",
      label: "Open new Firefox window", // Concise label
      content: "Open a new Firefox browser window.",
      category: "setup",
      metadata: {
        image_refs: [],
        ui_elements: ["Firefox browser application"],
        inputs: [],
        expected_result: "A new, empty Firefox browser window is open and active."
      },
    },
    position: { x: 100, y: 0 },
  },
  {
    id: "2",
    type: "custom",
    data: {
      id: "2",
      label: "Navigate to 'Find Bugs'",
      content: "Navigate to the 'Find Bugs' page by entering 'https://academybugs.com/find-bugs/' into the address bar and pressing Enter.",
      category: "action",
      metadata: {
        image_refs: [],
        ui_elements: ["Browser address bar"],
        inputs: ["url=https://academybugs.com/find-bugs/"],
        expected_result: "The AcademyBugs 'Find Bugs' page (https://academybugs.com/find-bugs/) is successfully loaded and displayed."
      },
    },
    position: { x: 100, y: 100 },
  },
  {
    id: "3",
    type: "custom",
    data: {
      id: "3",
      label: "Click first product",
      content: "On the 'Find Bugs' page, identify and click on the first available product link. For example, this might be 'DNK Yellow Shoes'.",
      category: "action",
      metadata: {
        image_refs: [],
        ui_elements: ["First product link on the page", "Example: 'DNK Yellow Shoes' link"],
        inputs: [],
        expected_result: "The browser navigates to the product detail page for the clicked product."
      },
    },
    position: { x: 100, y: 200 },
  },
  {
    id: "4",
    type: "custom",
    data: {
      id: "4",
      label: "Locate 'X' icon",
      content: "On the product detail page, locate the social media share icon for 'X' (formerly Twitter). This is typically represented by an 'X' logo or a bird logo.",
      category: "action",
      metadata: {
        image_refs: [],
        ui_elements: ["X (Twitter) social share icon/button"],
        inputs: [],
        expected_result: "The 'X' (Twitter) social share icon is visually identified on the page."
      },
    },
    position: { x: 100, y: 300 },
  },
  {
    id: "5",
    type: "custom",
    data: {
      id: "5",
      label: "Click 'X' icon",
      content: "Click the 'X' (Twitter) social share icon.",
      category: "action",
      metadata: {
        image_refs: [],
        ui_elements: ["X (Twitter) social share icon/button"],
        inputs: [],
        expected_result: "A new browser tab attempts to open or the current tab attempts to navigate to a Twitter sharing URL."
      },
    },
    position: { x: 100, y: 400 },
  },
  {
    id: "6",
    type: "custom",
    data: {
      id: "6",
      label: "Observe browser for error",
      content: "Observe the browser. Note any new tabs opened and error messages displayed. Specifically, look for a DNS error page.",
      category: "observation",
      metadata: {
        image_refs: [],
        ui_elements: ["Browser tab", "Error message display area"],
        inputs: [],
        expected_result: "A browser error page is displayed, typically in a new tab, showing a message like 'This site can't be reached' and 'DNS_PROBE_FINISHED_NXDOMAIN'."
      },
    },
    position: { x: 100, y: 500 },
  },
  {
    id: "7",
    type: "custom",
    data: {
      id: "7",
      label: "(Optional) DevTools check",
      content: "(Optional) Open browser developer tools (e.g., by pressing F12), navigate to the 'Console' and 'Network' tabs, and look for specific error details related to DNS resolution for the Twitter domain.",
      category: "verification",
      metadata: {
        image_refs: [],
        ui_elements: ["Browser developer tools", "Console tab", "Network tab"],
        inputs: [],
        expected_result: "Developer tools show errors indicating a failure to resolve the domain name associated with the Twitter share link."
      },
    },
    position: { x: 100, y: 600 },
  },
];

export const demoTaskGraphEdges = [
  { id: 'e1-2', source: '1', target: '2', style: { stroke: '#777', strokeWidth: 1.5, strokeDasharray: '5 5' }, markerEnd: { type: 'arrowclosed', width: 15, height: 15, color: '#777' } },
  { id: 'e2-3', source: '2', target: '3', style: { stroke: '#777', strokeWidth: 1.5, strokeDasharray: '5 5' }, markerEnd: { type: 'arrowclosed', width: 15, height: 15, color: '#777' } },
  { id: 'e3-4', source: '3', target: '4', style: { stroke: '#777', strokeWidth: 1.5, strokeDasharray: '5 5' }, markerEnd: { type: 'arrowclosed', width: 15, height: 15, color: '#777' } },
  { id: 'e4-5', source: '4', target: '5', style: { stroke: '#777', strokeWidth: 1.5, strokeDasharray: '5 5' }, markerEnd: { type: 'arrowclosed', width: 15, height: 15, color: '#777' } },
  { id: 'e5-6', source: '5', target: '6', style: { stroke: '#777', strokeWidth: 1.5, strokeDasharray: '5 5' }, markerEnd: { type: 'arrowclosed', width: 15, height: 15, color: '#777' } },
  { id: 'e6-7', source: '6', target: '7', style: { stroke: '#777', strokeWidth: 1.5, strokeDasharray: '5 5' }, markerEnd: { type: 'arrowclosed', width: 15, height: 15, color: '#777' } },
];

export const demoAgentLogs = [
  // Step 1 Logs
  `[STEP 1: Open a new Firefox browser window.]
Agent: I'll help you open a new Firefox browser window. Let me take a screenshot first to see the desktop, then I'll click on the Firefox icon.
Tool Use: computer
Input: {'action': 'screenshot'}
Observation: I can see the Firefox icon in the taskbar at the bottom of the screen. I'll click on it to open a new Firefox browser window.
Tool Use: computer
Input: {'action': 'left_click', 'coordinate': [802, 738]}
Observation: I can see that Firefox has opened, but it's showing a welcome wizard. As per the instructions, I should ignore this wizard and not click on any of the setup buttons. Instead, I'll click directly on the address bar.
Tool Use: computer
Input: {'action': 'left_click', 'coordinate': [294, 100]}
Result: Perfect! I now have Firefox open with the address bar focused, which shows I have successfully opened a new Firefox browser window. The welcome wizard is still present in the background, but as per instructions, I've ignored it and directly accessed the address bar where I can type URLs or search terms if needed.`,

  // Step 2 Logs
  `[STEP 2: Navigate to the 'Find Bugs' page]
Agent: I'll navigate to the 'Find Bugs' page by entering the URL in the address bar. Let me do that for you.
Tool Use: computer
Input: {'action': 'type', 'text': 'https://academybugs.com/find-bugs/'}
Tool Use: computer
Input: {'action': 'key', 'text': 'Return'}
Result: Great! I've successfully navigated to the AcademyBugs 'Find Bugs' page at https://academybugs.com/find-bugs/. The page has loaded correctly and displays... (details omitted for brevity here, but include full from email)`,

  // Step 3 Logs
  `[STEP 3: Click on the first available product link]
Agent: I'll identify and click on the first available product link on the 'Find Bugs' page. Looking at the current screenshot, I can see that the first product appears to be a pair of yellow shoes. Let me click on that product.
Tool Use: computer
Input: {'action': 'left_click', 'coordinate': [164, 551]}
Result: I have successfully clicked on the first product, which is indeed the "DNK Yellow Shoes" as suggested in the example. The browser has navigated to the product detail page as expected...`,
  
  // Step 4 Logs
  `[STEP 4: Locate the social media share icon for 'X']
Agent: I'll look for the social media share icon for 'X' (formerly Twitter) on the product detail page...
Tool Use: computer
Input: {'action': 'scroll', 'coordinate': [512, 400], 'scroll_amount': 5, 'scroll_direction': 'down'}
Result: Great! I can now see the social media sharing icons on the page...The X/Twitter icon is positioned approximately at coordinates [416, 241] on the page...`,

  // Step 5 Logs
  `[STEP 5: Click the 'X' (Twitter) social share icon.]
Agent: I'll click on the X (Twitter) social share icon that I identified in the previous step.
Tool Use: computer
Input: {'action': 'left_click', 'coordinate': [416, 241]}
Observation: I successfully clicked on the X (Twitter) social share icon, and as expected, the browser attempted to navigate to a Twitter sharing URL... However, we're seeing a "Server Not Found" error page... The URL appears to have a typo ("twitter.cointent" instead of "twitter.com/intent")... The bug is reproduced.`,

  // Step 6 Logs
  `[STEP 6: Observe the browser. Note any new tabs opened and error messages displayed.]
Agent: I'll observe the browser and note any error messages displayed, particularly looking for a DNS error page.
Result: Looking at the current screenshot, I can see that after clicking the X (Twitter) social share icon, the browser has displayed an error page... The page title shows "Server Not Found — Mozilla Firefox"...This is indeed a DNS error page...`,

  // Step 7 Logs
  `[STEP 7: (Optional) Open browser developer tools]
Agent: I'll open the browser developer tools to examine the specific error details related to the DNS resolution issue. I'll press F12 to open the developer tools.
Tool Use: computer
Input: {'action': 'key', 'text': 'F12'}
Observation: I've opened the developer tools, but I need to switch to the Network tab to examine the DNS resolution errors. Let me do that.
Tool Use: computer
Input: {'action': 'left_click', 'coordinate': [364, 471]}
Result: [Simulated observation of Network tab confirming NXDOMAIN or similar DNS error for twitter.cointent]`,

  // Final Verification Message
  `[BUG VERIFIED: DNS_PROBE_FINISHED_NXDOMAIN error (or equivalent via typo twitter.cointent) observed after clicking X/Twitter share link.]`
]; 