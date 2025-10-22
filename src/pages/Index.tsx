import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

interface KeyStats {
  key: string;
  count: number;
}

interface Session {
  id: string;
  startTime: Date;
  endTime?: Date;
  duration: number;
  keyCount: number;
}

const Index = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [keyStats, setKeyStats] = useState<KeyStats[]>([
    { key: 'A', count: 234 },
    { key: 'E', count: 189 },
    { key: 'Space', count: 167 },
    { key: 'T', count: 145 },
    { key: 'O', count: 123 },
    { key: 'Enter', count: 98 },
    { key: 'I', count: 87 },
    { key: 'N', count: 76 },
  ]);
  const [sessionTime, setSessionTime] = useState(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isRecording && currentSession) {
      interval = setInterval(() => {
        setSessionTime(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording, currentSession]);

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  const handleStartStop = () => {
    if (!isRecording) {
      const newSession: Session = {
        id: Date.now().toString(),
        startTime: new Date(),
        duration: 0,
        keyCount: 0
      };
      setCurrentSession(newSession);
      setIsRecording(true);
      setSessionTime(0);
    } else {
      if (currentSession) {
        const endedSession: Session = {
          ...currentSession,
          endTime: new Date(),
          duration: sessionTime,
          keyCount: Math.floor(Math.random() * 500) + 100
        };
        setSessions(prev => [endedSession, ...prev]);
        setCurrentSession(null);
      }
      setIsRecording(false);
      setSessionTime(0);
    }
  };

  const maxCount = Math.max(...keyStats.map(k => k.count));

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-foreground mb-2">Keyboard Logger</h1>
            <p className="text-muted-foreground">Отслеживайте активность клавиатуры</p>
          </div>
          <div className="flex items-center gap-3">
            <Icon name="Keyboard" size={32} className="text-primary" />
          </div>
        </div>

        <Card className="p-8 bg-card border-border">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-primary/20 flex items-center justify-center">
                <Icon name={isRecording ? "Activity" : "PlayCircle"} size={24} className="text-primary" />
              </div>
              <div>
                <h2 className="text-2xl font-semibold text-card-foreground">
                  {isRecording ? 'Запись активна' : 'Готов к записи'}
                </h2>
                <p className="text-muted-foreground text-sm">
                  {isRecording ? 'Все нажатия регистрируются' : 'Нажмите кнопку для начала'}
                </p>
              </div>
            </div>
            <Button
              onClick={handleStartStop}
              size="lg"
              className={`${isRecording ? 'bg-destructive hover:bg-destructive/90' : 'bg-primary hover:bg-primary/90'} px-8`}
            >
              <Icon name={isRecording ? "Square" : "Play"} size={20} className="mr-2" />
              {isRecording ? 'Остановить' : 'Начать запись'}
            </Button>
          </div>

          {isRecording && (
            <div className="space-y-4 mt-6 pt-6 border-t border-border">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Время сессии</span>
                <span className="text-3xl font-mono font-bold text-primary">{formatTime(sessionTime)}</span>
              </div>
            </div>
          )}
        </Card>

        <div className="grid md:grid-cols-2 gap-6">
          <Card className="p-6 bg-card border-border">
            <div className="flex items-center gap-3 mb-6">
              <Icon name="BarChart3" size={24} className="text-primary" />
              <h3 className="text-xl font-semibold text-card-foreground">Статистика клавиш</h3>
            </div>
            <div className="space-y-4">
              {keyStats.map((stat, index) => (
                <div key={stat.key} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className="w-20 justify-center font-mono">
                        {stat.key}
                      </Badge>
                      <span className="text-sm text-muted-foreground">#{index + 1}</span>
                    </div>
                    <span className="text-lg font-semibold text-card-foreground">{stat.count}</span>
                  </div>
                  <Progress value={(stat.count / maxCount) * 100} className="h-2" />
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6 bg-card border-border">
            <div className="flex items-center gap-3 mb-6">
              <Icon name="History" size={24} className="text-primary" />
              <h3 className="text-xl font-semibold text-card-foreground">История сессий</h3>
            </div>
            <div className="space-y-3 max-h-[500px] overflow-y-auto">
              {sessions.length === 0 ? (
                <div className="text-center py-12">
                  <Icon name="Inbox" size={48} className="mx-auto text-muted-foreground/50 mb-3" />
                  <p className="text-muted-foreground">Нет записанных сессий</p>
                  <p className="text-sm text-muted-foreground/70">Начните запись для создания истории</p>
                </div>
              ) : (
                sessions.map((session) => (
                  <div
                    key={session.id}
                    className="p-4 rounded-lg bg-muted/30 border border-border hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Icon name="Circle" size={8} className="text-primary fill-primary" />
                        <span className="text-sm font-medium text-card-foreground">
                          {formatDate(session.startTime)}
                        </span>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {session.keyCount} клавиш
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground ml-4">
                      <div className="flex items-center gap-1">
                        <Icon name="Clock" size={14} />
                        <span>{formatTime(session.duration)}</span>
                      </div>
                      {session.endTime && (
                        <div className="flex items-center gap-1">
                          <Icon name="CheckCircle2" size={14} />
                          <span>Завершено</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Index;
