import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './AIChatModal.css';

const AIChatModal = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        { sender: 'ai', text: 'Hello! I am your SnapShop AI Assistant. How can I help you today?' }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const toggleModal = () => {
        setIsOpen(!isOpen);
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage = { sender: 'user', text: input };
        const updatedMessages = [...messages, userMessage];
        setMessages(updatedMessages);
        setInput('');
        setIsLoading(true);

        try {
            // Adjust the URL if the backend is hosted elsewhere
            const response = await axios.post('/api/ai-chat', { history: updatedMessages }, { withCredentials: true });
            
            if (response.data.status === 'success') {
                setMessages((prev) => [...prev, { sender: 'ai', text: response.data.response }]);
            } else {
                setMessages((prev) => [...prev, { sender: 'ai', text: "Sorry, I couldn't process that right now." }]);
            }
        } catch (error) {
            console.error("AI Chat Error:", error);
            setMessages((prev) => [...prev, { sender: 'ai', text: "An error occurred while connecting to the AI assistant." }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            {/* Floating Action Button */}
            <button className={`ai-fab ${isOpen ? 'open' : ''}`} onClick={toggleModal}>
                {isOpen ? '✕' : '✨ Ask AI'}
            </button>

            {/* Chat Modal */}
            <div className={`ai-chat-modal ${isOpen ? 'open' : ''}`}>
                <div className="ai-chat-header">
                    <h3>SnapShop Assistant</h3>
                </div>
                
                <div className="ai-chat-body">
                    {messages.map((msg, index) => (
                        <div key={index} className={`ai-message-row ${msg.sender}`}>
                            <div className={`ai-message ${msg.sender}`}>
                                {msg.sender === 'ai' ? (
                                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                                ) : (
                                    msg.text
                                )}
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="ai-message-row ai">
                            <div className="ai-message ai loading">
                                <span className="dot"></span>
                                <span className="dot"></span>
                                <span className="dot"></span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
                
                <form className="ai-chat-footer" onSubmit={handleSend}>
                    <input 
                        type="text" 
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask about products, discounts..." 
                        disabled={isLoading}
                    />
                    <button type="submit" disabled={isLoading || !input.trim()}>
                        Send
                    </button>
                </form>
            </div>
        </>
    );
};

export default AIChatModal;
