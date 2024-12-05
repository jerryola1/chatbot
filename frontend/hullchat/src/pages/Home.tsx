import React from 'react';
import {
    IonContent,
    IonPage,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonCard,
    IonCardContent,
    IonIcon,
    IonText,
    IonButton
} from '@ionic/react';
import { chatbubbleEllipsesOutline, schoolOutline, libraryOutline, calendarOutline } from 'ionicons/icons';
import { useHistory } from 'react-router-dom';
import './Home.css';

const Home: React.FC = () => {
    const history = useHistory();

    const handleChatClick = () => {
        history.push('/chat');
    };

    return (
        <IonPage>
            <IonContent className="ion-padding">
                <div className="home-container">
                    <IonHeader>
                        <IonToolbar>
                            <IonTitle>Hull AI Assistant</IonTitle>
                        </IonToolbar>
                    </IonHeader>

                    <div className="welcome-section">
                        <h1>Welcome to Hull AI</h1>
                        <p>Your intelligent assistant for university information</p>
                    </div>

                    <div className="features-grid">
                        <IonCard className="feature-card" onClick={handleChatClick}>
                            <IonCardContent>
                                <IonIcon icon={chatbubbleEllipsesOutline} className="feature-icon" />
                                <IonText>
                                    <h2>Chat Assistant</h2>
                                    <p>Get instant answers to your questions</p>
                                </IonText>
                            </IonCardContent>
                        </IonCard>

                        <IonCard className="feature-card">
                            <IonCardContent>
                                <IonIcon icon={schoolOutline} className="feature-icon" />
                                <IonText>
                                    <h2>Academic Support</h2>
                                    <p>Access study resources and guidance</p>
                                </IonText>
                            </IonCardContent>
                        </IonCard>

                        <IonCard className="feature-card">
                            <IonCardContent>
                                <IonIcon icon={libraryOutline} className="feature-icon" />
                                <IonText>
                                    <h2>Library Services</h2>
                                    <p>Find books and research materials</p>
                                </IonText>
                            </IonCardContent>
                        </IonCard>

                        <IonCard className="feature-card">
                            <IonCardContent>
                                <IonIcon icon={calendarOutline} className="feature-icon" />
                                <IonText>
                                    <h2>Events & Schedules</h2>
                                    <p>Stay updated with university events</p>
                                </IonText>
                            </IonCardContent>
                        </IonCard>
                    </div>

                    <div className="start-chat-section">
                        <IonButton 
                            expand="block" 
                            className="start-chat-button"
                            onClick={handleChatClick}
                        >
                            Start Chatting
                        </IonButton>
                    </div>
                </div>
            </IonContent>
        </IonPage>
    );
};

export default Home;
