import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { BookOpen, CalendarDays, Send } from 'lucide-react'
import { cancelEvent, createSession, getCourses, getEvents, getMessages, registerEvent, sendMessage } from '@/api/customer-service'
import PageHeader from '@/components/shared/PageHeader'
import LoadingState from '@/components/shared/LoadingState'
import ErrorState from '@/components/shared/ErrorState'
import EmptyState from '@/components/shared/EmptyState'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function CustomerServicePage() {
  const qc = useQueryClient(); const [sessionId, setSessionId] = useState(''); const [content, setContent] = useState('')
  const session = useMutation({ mutationFn: createSession, onSuccess: (x) => setSessionId(x.session_id) })
  useEffect(() => { if (!sessionId && !session.isPending && !session.isError) session.mutate() }, [sessionId]) // eslint-disable-line react-hooks/exhaustive-deps
  const messages = useQuery({ queryKey: ['chat', sessionId], queryFn: () => getMessages(sessionId), enabled: !!sessionId })
  const courses = useQuery({ queryKey: ['courses'], queryFn: getCourses }); const events = useQuery({ queryKey: ['events'], queryFn: getEvents })
  const send = useMutation({ mutationFn: () => sendMessage(sessionId, content.trim()), onSuccess: async () => { setContent(''); await qc.invalidateQueries({ queryKey: ['chat', sessionId] }) } })
  const event = useMutation({ mutationFn: ({ id, cancel }: { id: number; cancel: boolean }) => cancel ? cancelEvent(id) : registerEvent(id), onSuccess: async () => qc.invalidateQueries({ queryKey: ['events'] }) })
  return <div><PageHeader title="客服咨询" description="查看课程与活动，并保存当前账号自己的咨询会话。" /><div className="grid gap-6 xl:grid-cols-[1.3fr_.7fr]"><Card><CardHeader><CardTitle>咨询会话</CardTitle></CardHeader><CardContent><div className="min-h-80 space-y-3">{session.isPending && <LoadingState text="正在建立会话…" />}{session.isError && <ErrorState onRetry={() => session.mutate()} />}{messages.data?.items.length === 0 && <EmptyState title="开始咨询" description="输入问题后，消息会保存到你的个人会话。" />}{messages.data?.items.map((m) => <div key={m.id} className={`max-w-[85%] rounded-lg p-3 text-sm ${m.role === 'user' ? 'ml-auto bg-primary text-primary-foreground' : 'bg-muted'}`}>{m.content}</div>)}</div><form className="mt-4 flex gap-2" onSubmit={(e) => { e.preventDefault(); if (content.trim()) send.mutate() }}><label className="sr-only" htmlFor="chat-message">咨询内容</label><Input id="chat-message" value={content} onChange={(e) => setContent(e.target.value)} placeholder="输入咨询内容…" /><Button type="submit" disabled={!sessionId || !content.trim() || send.isPending} aria-label="发送消息"><Send /></Button></form></CardContent></Card><div className="space-y-6"><Card><CardHeader><CardTitle className="flex gap-2"><BookOpen />课程</CardTitle></CardHeader><CardContent>{courses.isLoading && <LoadingState />}{courses.isError && <ErrorState onRetry={() => courses.refetch()} />}{courses.data?.items.map((x) => <article key={x.id} className="border-b py-3"><p className="font-medium">{x.project_name}</p><p className="text-xs text-muted-foreground">{x.description || x.category || '暂无简介'}</p></article>)}</CardContent></Card><Card><CardHeader><CardTitle className="flex gap-2"><CalendarDays />近期活动</CardTitle></CardHeader><CardContent>{events.data?.items.map((x) => <article key={x.id} className="border-b py-3"><p className="font-medium">{x.event_name}</p><p className="text-xs text-muted-foreground">{new Date(x.start_time).toLocaleString()} · {x.location || '线上'}</p><div className="mt-2 flex gap-2"><Button size="sm" onClick={() => event.mutate({ id: x.id, cancel: false })}>报名</Button><Button size="sm" variant="outline" onClick={() => event.mutate({ id: x.id, cancel: true })}>取消</Button></div></article>)}</CardContent></Card></div></div></div>
}
