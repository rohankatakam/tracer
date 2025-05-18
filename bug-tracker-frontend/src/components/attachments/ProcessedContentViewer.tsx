import React, { useState, useEffect } from 'react';
import { attachmentAPI } from '../../services/api-client';

interface ProcessedContentViewerProps {
  attachmentId: string;
}

interface ProcessedContentState {
  isLoading: boolean;
  error: string | null;
  data: any | null;
  processingStatus: string;
  activeTab: string;
  activeTextContent: any | null;
  activeImageContent: any | null;
}

export const ProcessedContentViewer: React.FC<ProcessedContentViewerProps> = ({ 
  attachmentId 
}) => {
  const [state, setState] = useState<ProcessedContentState>({
    isLoading: true,
    error: null,
    data: null,
    processingStatus: 'unknown',
    activeTab: 'summary',
    activeTextContent: null,
    activeImageContent: null
  });
  
  const fetchProcessedContent = async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const data = await attachmentAPI.getProcessedContent(attachmentId);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: null,
        data,
        processingStatus: data.processing_status || 'unknown'
      }));
    } catch (error) {
      console.error('Error fetching processed content:', error);
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: 'Failed to load processed content. Please try again.' 
      }));
    }
  };
  
  const triggerProcessing = async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const result = await attachmentAPI.processAttachment(attachmentId);
      setState(prev => ({ 
        ...prev, 
        processingStatus: 'processing',
        isLoading: false
      }));
      
      // If processing was started asynchronously, poll for completion
      if (result.status === 'pending') {
        setTimeout(fetchProcessedContent, 3000);
      } else {
        // If processing was done synchronously, update with results
        fetchProcessedContent();
      }
    } catch (error) {
      console.error('Error triggering processing:', error);
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: 'Failed to process attachment. Please try again.' 
      }));
    }
  };
  
  useEffect(() => {
    fetchProcessedContent();
  }, [attachmentId]);
  
  if (state.isLoading) {
    return <div className="flex justify-center py-4"><div className="loader"></div></div>;
  }
  
  if (state.error) {
    return (
      <div className="text-red-500 p-4 text-center">
        <p>{state.error}</p>
        <button 
          onClick={fetchProcessedContent}
          className="mt-2 px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Try Again
        </button>
      </div>
    );
  }
  
  if (!state.data) {
    return (
      <div className="text-gray-500 p-4 text-center">
        No processed content available
      </div>
    );
  }
  
  if (state.processingStatus === 'pending' || state.processingStatus === 'processing') {
    return (
      <div className="text-blue-500 p-4 text-center">
        <p>Processing in progress...</p>
        <div className="mt-2">
          <div className="loader"></div>
        </div>
        <button 
          onClick={fetchProcessedContent}
          className="mt-4 px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Check Status
        </button>
      </div>
    );
  }
  
  if (state.processingStatus === 'failed') {
    return (
      <div className="text-red-500 p-4 text-center">
        <p>Processing failed. Please try again.</p>
        <button 
          onClick={triggerProcessing}
          className="mt-2 px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Process Now
        </button>
      </div>
    );
  }
  
  // Main content display for successfully processed content
  return (
    <div className="p-4">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Processed Content</h3>
      
      {/* File metadata */}
      <div className="bg-gray-50 p-3 rounded mb-4">
        <h4 className="font-medium mb-2">File Information</h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>Filename:</div>
          <div>{state.data.filename}</div>
          <div>Type:</div>
          <div>{state.data.file_type}</div>
          <div>Processed at:</div>
          <div>{new Date(state.data.processed_at).toLocaleString()}</div>
        </div>
      </div>
      
      {/* PDF Information */}
      {state.data.pdf_content && (
        <div className="bg-gray-50 p-3 rounded mb-4">
          <h4 className="font-medium mb-2">PDF Information</h4>
          <div className="bg-white border rounded p-3">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>Title:</div>
              <div>{state.data.pdf_content.title || 'N/A'}</div>
              <div>Author:</div>
              <div>{state.data.pdf_content.author || 'N/A'}</div>
              <div>Pages:</div>
              <div>{state.data.pdf_content.num_pages}</div>
              {state.data.pdf_content.metadata && state.data.pdf_content.metadata.creation_date && (
                <>
                  <div>Creation Date:</div>
                  <div>{state.data.pdf_content.metadata.creation_date}</div>
                </>
              )}
            </div>
            <div className="mt-3">
              <div className="text-sm font-medium mb-1">Content Summary:</div>
              <div className="text-sm">
                <ul className="list-disc pl-5 text-xs space-y-1">
                  <li>
                    {state.data.pdf_content.metadata?.text_extraction_count || state.data.text_contents?.length || 0} text extractions from {state.data.pdf_content.num_pages} pages
                  </li>
                  <li>
                    {state.data.pdf_content.metadata?.image_extraction_count || state.data.image_contents?.length || 0} images extracted
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Display extracted content with tabs */}
      {(state.data.pdf_content || 
        (state.data.text_contents && state.data.text_contents.length > 0) || 
        (state.data.image_contents && state.data.image_contents.length > 0)) && (
        <div className="mt-4">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-4" aria-label="Tabs">
              <button
                onClick={() => setState(prev => ({ ...prev, activeTab: 'summary' }))}
                className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                  state.activeTab === 'summary'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Summary
              </button>
              {(state.data.text_contents?.length > 0 || state.data.pdf_content?.metadata?.text_extraction_count > 0) && (
                <button
                  onClick={() => setState(prev => ({ ...prev, activeTab: 'text' }))}
                  className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                    state.activeTab === 'text'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Text Content
                </button>
              )}
              {(state.data.image_contents?.length > 0 || state.data.pdf_content?.metadata?.image_extraction_count > 0) && (
                <button
                  onClick={() => setState(prev => ({ ...prev, activeTab: 'images' }))}
                  className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                    state.activeTab === 'images'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Images
                </button>
              )}
            </nav>
          </div>
          
          {/* Tab content */}
          <div className="mt-4">
            {/* Summary Tab */}
            {state.activeTab === 'summary' && (
              <div className="text-sm">
                <h3 className="font-medium mb-2">Content Overview</h3>
                <p className="mb-2">
                  This document contains {state.data.pdf_content?.num_pages || 0} pages with
                  {' '}{state.data.pdf_content?.metadata?.text_extraction_count || state.data.text_contents?.length || 0} text extractions and
                  {' '}{state.data.pdf_content?.metadata?.image_extraction_count || state.data.image_contents?.length || 0} images.
                </p>
                <p className="text-xs text-gray-500">
                  Use the tabs above to view extracted content.
                </p>
              </div>
            )}
            
            {/* Text Content Tab */}
            {state.activeTab === 'text' && (
              <div>
                <h3 className="font-medium mb-2">Extracted Text</h3>
                {/* Show default message if we have text extraction counts but no actual content in the API */}
                {(state.data.pdf_content?.metadata?.text_extraction_count > 0 && (!state.data.text_contents || state.data.text_contents.length === 0)) ? (
                  <div className="bg-gray-50 p-3 rounded border">
                    <p className="text-sm">There are {state.data.pdf_content.metadata.text_extraction_count} text extractions in this document.</p>
                    <p className="text-xs text-gray-500 mt-2">The text content is not included in the API response for performance reasons. Please use the RefreshWithContent button below to load the full content.</p>
                    <button 
                      onClick={() => alert('This feature will be implemented in a future update.')}
                      className="mt-3 px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600"
                    >
                      RefreshWithContent
                    </button>
                  </div>
                ) : state.data.text_contents && state.data.text_contents.length > 0 ? (
                  <div>
                    <div className="flex flex-wrap gap-2 mb-4">
                      {state.data.text_contents.map((text: any, index: number) => (
                        <button
                          key={text.id}
                          onClick={() => setState(prev => ({ ...prev, activeTextContent: text }))}
                          className={`px-3 py-1 text-xs rounded-full ${
                            state.activeTextContent?.id === text.id
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-200 hover:bg-gray-300 text-gray-800'
                          }`}
                        >
                          Text {index + 1}
                        </button>
                      ))}
                    </div>
                    {state.activeTextContent ? (
                      <div className="bg-gray-50 p-3 rounded border">
                        <div className="mb-2 text-xs text-gray-500">
                          <span className="font-medium">Method:</span> {state.activeTextContent.extraction_method || 'Unknown'}
                          {state.activeTextContent.language && (
                            <span className="ml-3">
                              <span className="font-medium">Language:</span> {state.activeTextContent.language}
                            </span>
                          )}
                        </div>
                        <div className="whitespace-pre-wrap bg-white p-2 border rounded text-sm">
                          {state.activeTextContent.content || 'No content available'}
                        </div>
                      </div>
                    ) : (
                      <div className="text-gray-500 text-center py-4">
                        Select a text extraction to view
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-gray-500 text-center py-4">
                    No text content available
                  </div>
                )}
              </div>
            )}
            
            {/* Images Tab */}
            {state.activeTab === 'images' && (
              <div>
                <h3 className="font-medium mb-2">Extracted Images</h3>
                {/* Show default message if we have image extraction counts but no actual content in the API */}
                {(state.data.pdf_content?.metadata?.image_extraction_count > 0 && (!state.data.image_contents || state.data.image_contents.length === 0)) ? (
                  <div className="bg-gray-50 p-3 rounded border">
                    <p className="text-sm">There are {state.data.pdf_content.metadata.image_extraction_count} images in this document.</p>
                    <p className="text-xs text-gray-500 mt-2">The image content is not included in the API response for performance reasons. Please use the RefreshWithContent button below to load the full content.</p>
                    <button 
                      onClick={() => alert('This feature will be implemented in a future update.')}
                      className="mt-3 px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600"
                    >
                      RefreshWithContent
                    </button>
                  </div>
                ) : state.data.image_contents && state.data.image_contents.length > 0 ? (
                  <div>
                    <div className="flex flex-wrap gap-2 mb-4">
                      {state.data.image_contents.map((image: any, index: number) => (
                        <button
                          key={image.id}
                          onClick={() => setState(prev => ({ ...prev, activeImageContent: image }))}
                          className={`px-3 py-1 text-xs rounded-full ${
                            state.activeImageContent?.id === image.id
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-200 hover:bg-gray-300 text-gray-800'
                          }`}
                        >
                          Image {index + 1}
                        </button>
                      ))}
                    </div>
                    {state.activeImageContent ? (
                      <div className="bg-gray-50 p-3 rounded border">
                        <div className="mb-2 text-xs text-gray-500">
                          {state.activeImageContent.ocr_confidence && (
                            <div>
                              <span className="font-medium">OCR Confidence:</span> {Math.round(state.activeImageContent.ocr_confidence * 100)}%
                            </div>
                          )}
                        </div>
                        {state.activeImageContent.file_path ? (
                          <div className="flex justify-center">
                            <div className="relative max-w-full border rounded overflow-hidden">
                              <img
                                src={`http://localhost:8080/attachments/file/${encodeURIComponent(state.activeImageContent.file_path)}`}
                                alt={`Extracted image ${state.activeImageContent.id}`}
                                className="max-w-full max-h-[400px] object-contain"
                              />
                            </div>
                          </div>
                        ) : (
                          <div className="text-gray-500 text-center py-4">
                            Image preview not available
                          </div>
                        )}
                        {state.activeImageContent.ocr_text_id && (
                          <div className="mt-3">
                            <h4 className="text-sm font-medium mb-1">OCR Text:</h4>
                            <div className="whitespace-pre-wrap bg-white p-2 border rounded text-sm max-h-[200px] overflow-y-auto">
                              {state.data.text_contents?.find((t: any) => t.id === state.activeImageContent.ocr_text_id)?.content || 'OCR text not available'}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-gray-500 text-center py-4">
                        Select an image to view
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-gray-500 text-center py-4">
                    No image content available
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* No content case */}
      {(!state.data.text_contents || state.data.text_contents.length === 0) && 
       (!state.data.image_contents || state.data.image_contents.length === 0) && 
       !state.data.pdf_content && (
        <div className="text-gray-500 text-center py-4">
          No content was extracted from this file.
        </div>
      )}
      
      <div className="mt-4 flex justify-end">
        <button
          onClick={fetchProcessedContent}
          className="px-3 py-1 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
        >
          Refresh
        </button>
      </div>
    </div>
  );
};
