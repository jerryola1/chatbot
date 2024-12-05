import { useState, useRef, useEffect } from 'react';
import {
    IonContent,
    IonPage,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonButtons,
    IonButton,
    IonIcon,
    IonCard,
    IonCardContent,
    IonText,
    IonNote,
    IonTextarea,
} from '@ionic/react';
import { chevronBackCircleOutline, ellipsisVerticalOutline, addCircleOutline, paperPlaneOutline, thumbsUpOutline, thumbsDownOutline, copyOutline } from 'ionicons/icons';
import { useHistory } from 'react-router-dom';
import './Chat.css';
import { format } from 'date-fns';
import axios from 'axios';

interface Message {
    id: string;
    text: string;
    isUser: boolean;
    timestamp: Date;
}

interface ApiResponse {
    response: string;
    error?: string;
}

const Chat: React.FC = () => {
    const history = useHistory();
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            text: 'Hi! Welcome to Hull ChatBot.\nHow can I help you today?',
            isUser: false,
            timestamp: new Date()
        }
    ]);
    const [inputText, setInputText] = useState('');
    const messageContainerRef = useRef<HTMLDivElement>(null);
    const [currentTime, setCurrentTime] = useState(new Date());
    const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentTime(new Date());
        }, 60000);
        return () => clearInterval(interval);
    }, []);

    const getTimeString = (timestamp: Date) => {
        const diffInMinutes = Math.floor((currentTime.getTime() - timestamp.getTime()) / 60000);
        
        if (diffInMinutes < 1) return 'Just now';
        if (diffInMinutes === 1) return '1 min ago';
        if (diffInMinutes < 60) return `${diffInMinutes} mins ago`;
        return format(timestamp, 'h:mm a');
    };

    const handleBack = () => {
        history.push('/home');
    };

    const handleSend = async () => {
        if (inputText.trim()) {
            const userMessage: Message = {
                id: Date.now().toString(),
                text: inputText.trim(),
                isUser: true,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, userMessage]);
            setInputText('');

            // Scroll to new message with padding
            const scrollToNewMessage = () => {
                if (messageContainerRef.current) {
                    const lastMessage = messageContainerRef.current.lastElementChild;
                    if (lastMessage) {
                        const scrollPosition = lastMessage.getBoundingClientRect().bottom + 
                            messageContainerRef.current.scrollTop - 
                            messageContainerRef.current.clientHeight + 100; // 100px padding from bottom
                        
                        messageContainerRef.current.scrollTo({
                            top: scrollPosition,
                            behavior: 'smooth'
                        });
                    }
                }
            };

            // Scroll after user message
            setTimeout(scrollToNewMessage, 100);

            try {
                const response = await axios.post<ApiResponse>('https://hull-chat--example-llm-model-chat.modal.run', {
                    prompt: userMessage.text
                });

                setMessages(prev => [...prev, {
                    id: Date.now().toString(),
                    text: response.data.response,
                    isUser: false,
                    timestamp: new Date()
                }]);

                // Scroll after bot response
                setTimeout(scrollToNewMessage, 100);

            } catch (error) {
                console.error('Error:', error);
                setMessages(prev => [...prev, {
                    id: Date.now().toString(),
                    text: 'Sorry, I encountered an error. Please try again.',
                    isUser: false,
                    timestamp: new Date()
                }]);

                // Scroll after error message
                setTimeout(scrollToNewMessage, 100);
            }
        }
    };

    const handleCopy = (text: string, messageId: string) => {
        navigator.clipboard.writeText(text)
            .then(() => {
                setCopiedMessageId(messageId);
                setTimeout(() => {
                    setCopiedMessageId(null);
                }, 1000);
            })
            .catch(err => {
                console.error('Failed to copy text: ', err);
            });
    };

    return (
        <IonPage>
            <IonContent className="ion-padding">
                <div className="chat-mobile-container">
                    <IonHeader>
                        <IonToolbar>
                            <IonButtons slot="start">
                                <IonButton onClick={handleBack}>
                                    <IonIcon slot="icon-only" icon={chevronBackCircleOutline} className="header-icon" />
                                </IonButton>
                            </IonButtons>
                            <IonTitle>AI Chat</IonTitle>
                            <IonButtons slot="end">
                                <IonButton>
                                    <IonIcon slot="icon-only" icon={ellipsisVerticalOutline} className="header-icon" />
                                </IonButton>
                            </IonButtons>
                        </IonToolbar>
                    </IonHeader>

                    <div className="chat-content">
                        <div className="message-container" ref={messageContainerRef}>
                            {messages.map(message => (
                                <IonCard 
                                    key={message.id} 
                                    className={`message-card ${message.isUser ? 'user-message' : 'bot-message'}`}
                                >
                                    <IonCardContent>
                                        <div className="message-text">
                                            {message.text.split('\n').map((line, i) => (
                                                <div key={i}>{line}</div>
                                            ))}
                                        </div>
                                        <div className="message-footer">
                                            {!message.isUser && (
                                                <div className="message-actions">
                                                    <IonButton fill="clear" size="small" className="action-button">
                                                        <IonIcon icon={thumbsUpOutline} />
                                                    </IonButton>
                                                    <IonButton fill="clear" size="small" className="action-button">
                                                        <IonIcon icon={thumbsDownOutline} />
                                                    </IonButton>
                                                    <IonButton 
                                                        fill="clear" 
                                                        size="small" 
                                                        className="action-button"
                                                        onClick={() => handleCopy(message.text, message.id)}
                                                    >
                                                        <IonIcon 
                                                            icon={copyOutline} 
                                                            className={copiedMessageId === message.id ? 'copy-success' : ''}
                                                        />
                                                    </IonButton>
                                                </div>
                                            )}
                                            <IonNote className="message-time">
                                                {getTimeString(message.timestamp)}
                                            </IonNote>
                                        </div>
                                    </IonCardContent>
                                </IonCard>
                            ))}
                        </div>
                    </div>

                    <div className="input-container">
                        <IonButton fill="clear" className="input-button">
                            <IonIcon icon={addCircleOutline} slot="icon-only" />
                        </IonButton>
                        <div className="input-wrapper">
                            <IonTextarea
                                placeholder="Ask anything..."
                                className="message-input"
                                value={inputText}
                                onIonInput={e => setInputText(e.detail.value || '')}
                                onKeyDown={e => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        handleSend();
                                    }
                                }}
                                autoGrow
                                rows={1}
                                maxlength={1000}
                            />
                        </div>
                        <IonButton 
                            fill="clear" 
                            className="input-button"
                            onClick={handleSend}
                            disabled={!inputText.trim()}
                        >
                            <IonIcon icon={paperPlaneOutline} slot="icon-only" />
                        </IonButton>
                    </div>
                </div>
            </IonContent>
        </IonPage>
    );
};

export default Chat; 