import React, { useState } from 'react'
import {
  ChefHat,
  Send,
  Mic,
  Sparkles,
  Flame,
  Clock,
  Plus,
  Bot,
  User,
  Calculator,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { mockDishes, mockCookingHistory } from '@/utils/mockData'
import { cookingService } from '@/services/cooking.service'
import type { ChatMessage, Dish } from '@/types'
import { formatGrams } from '@/utils/cn'

export function CookingAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        'Namaste Chef Arjun! 👨‍🍳 I am your SafeGas AI Cooking Assistant. Ask me how much gas a dish will use, or ask for cooking tips to save LPG!',
      timestamp: new Date().toISOString(),
    },
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isListening, setIsListening] = useState(false)

  // Estimation Calculator State
  const [selectedDishes, setSelectedDishes] = useState<number[]>([1, 2])

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!inputMessage.trim()) return

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMsg])
    const prompt = inputMessage
    setInputMessage('')
    setIsTyping(true)

    try {
      const reply = await cookingService.chat(prompt)
      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: reply,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, botMsg])
    } catch {
      // fallback
    } finally {
      setIsTyping(false)
    }
  }

  const toggleDishSelection = (dishId: number) => {
    setSelectedDishes((prev) =>
      prev.includes(dishId) ? prev.filter((id) => id !== dishId) : [...prev, dishId]
    )
  }

  const estimatedTotalGas = selectedDishes.reduce((sum, id) => {
    const d = mockDishes.find((item) => item.id === id)
    return sum + (d?.base_gas_g || 0)
  }, 0)

  const estimatedTotalTime = selectedDishes.reduce((sum, id) => {
    const d = mockDishes.find((item) => item.id === id)
    return sum + (d?.base_duration_min || 0)
  }, 0)

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 card-shadow">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
            <ChefHat className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">AI Cooking Assistant & Gas Estimator</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Plan meals, estimate LPG consumption in grams, and chat for cooking efficiency tips.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat UI Column (2 Cols) */}
        <Card className="lg:col-span-2 flex flex-col h-[560px]">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Bot className="h-4 w-4 text-primary" />
              Kitchen AI Assistant Chat
            </h3>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-primary/10 text-primary">
              Gemini 2.5 Flash
            </span>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-1 scrollbar-hide">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3 text-xs ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {m.role === 'assistant' && (
                  <div className="h-8 w-8 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0">
                    <Bot className="h-4 w-4" />
                  </div>
                )}
                <div
                  className={`max-w-md p-3.5 rounded-2xl ${
                    m.role === 'user'
                      ? 'bg-primary text-white rounded-br-none'
                      : 'bg-slate-100 dark:bg-slate-700/60 text-slate-800 dark:text-slate-100 rounded-bl-none'
                  }`}
                >
                  <p className="leading-relaxed">{m.content}</p>
                </div>
                {m.role === 'user' && (
                  <div className="h-8 w-8 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center shrink-0 font-bold">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="flex items-center gap-2 text-xs text-slate-400 animate-pulse">
                <Bot className="h-4 w-4 text-primary" />
                <span>Chef AI is thinking...</span>
              </div>
            )}
          </div>

          {/* Suggested Prompt Chips */}
          <div className="py-2 flex items-center gap-2 overflow-x-auto scrollbar-hide">
            {['How much gas for Dal Tadka?', 'Tips to save gas', 'Estimate Biryani gas'].map((prompt) => (
              <button
                key={prompt}
                onClick={() => {
                  setInputMessage(prompt)
                }}
                className="px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 text-[11px] font-medium text-slate-600 dark:text-slate-300 shrink-0 transition-colors"
              >
                ✨ {prompt}
              </button>
            ))}
          </div>

          {/* Input Form */}
          <form onSubmit={handleSendMessage} className="pt-2 flex items-center gap-2 border-t border-slate-100 dark:border-slate-700/60">
            <button
              type="button"
              onClick={() => setIsListening(!isListening)}
              className={`p-2.5 rounded-xl border transition-colors ${
                isListening
                  ? 'bg-red-100 border-red-300 text-danger animate-pulse'
                  : 'bg-slate-50 dark:bg-slate-700/50 border-slate-200 dark:border-slate-600 text-slate-400'
              }`}
              title="Voice Input (UI)"
            >
              <Mic className="h-4 w-4" />
            </button>

            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask anything about recipes or gas savings..."
              className="flex-1"
            />

            <Button type="submit" size="md" rightIcon={<Send className="h-4 w-4" />}>
              Send
            </Button>
          </form>
        </Card>

        {/* Gas Estimation Calculator & Today's Plan (1 Col) */}
        <div className="space-y-6">
          {/* Gas Calculator */}
          <Card>
            <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
              <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <Calculator className="h-4 w-4 text-primary" />
                Gas Estimator Calculator
              </h3>
            </div>

            <p className="text-xs text-slate-500 mb-3">Select planned dishes for meal estimation:</p>

            <div className="space-y-2 max-h-44 overflow-y-auto pr-1 scrollbar-hide">
              {mockDishes.map((dish: Dish) => {
                const isSelected = selectedDishes.includes(dish.id)
                return (
                  <button
                    key={dish.id}
                    onClick={() => toggleDishSelection(dish.id)}
                    className={`w-full p-2.5 rounded-xl border text-left text-xs flex items-center justify-between transition-colors ${
                      isSelected
                        ? 'border-primary bg-primary/10 text-slate-900 dark:text-white font-bold'
                        : 'border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/30 text-slate-600 dark:text-slate-300'
                    }`}
                  >
                    <span>{dish.dish_name} ({dish.cuisine_tag})</span>
                    <span className="text-[11px] text-slate-400 font-semibold">{dish.base_gas_g}g &bull; {dish.base_duration_min}m</span>
                  </button>
                )
              })}
            </div>

            <div className="mt-4 p-3 rounded-xl bg-slate-100 dark:bg-slate-700/60 flex items-center justify-between text-xs">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Total Estimated Gas</span>
                <span className="text-base font-extrabold text-primary">{formatGrams(estimatedTotalGas)}</span>
              </div>
              <div className="text-right">
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Est. Duration</span>
                <span className="text-base font-extrabold text-slate-800 dark:text-slate-200">{estimatedTotalTime} Mins</span>
              </div>
            </div>
          </Card>

          {/* Today's Cooking History Log */}
          <Card>
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
              <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <Clock className="h-4 w-4 text-amber-500" />
                Today's Cooking Log
              </h3>
              <Button size="sm" variant="ghost" className="h-7 text-xs">
                <Plus className="h-3.5 w-3.5" /> Log
              </Button>
            </div>

            <div className="space-y-3">
              {mockCookingHistory.map((h) => (
                <div key={h.id} className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-700/40 text-xs flex items-center justify-between">
                  <div>
                    <p className="font-bold text-slate-800 dark:text-slate-100">{h.dish?.dish_name || 'Generic Cooking'}</p>
                    <span className="text-[10px] text-slate-400">Logged today</span>
                  </div>
                  <div className="text-right">
                    <span className="font-extrabold text-amber-500 block">{h.actual_gas_g}g</span>
                    <span className="text-[10px] text-slate-400">{h.actual_duration_min} mins</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
