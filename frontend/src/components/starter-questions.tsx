import { ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/card";

const starterQuestions = [
  "What is Lyzr Agent Studio?",
  "How to build AI agents with low-code platforms?",
  "How does RAG improve AI accuracy?",
  "What is AI hallucination?",
  "What are the benefits of multi-agent orchestration?",
];

export const StarterQuestionsList = ({
  handleSend,
}: {
  handleSend: (question: string) => void;
}) => {
  return (
    <div className="w-full mt-4">
      {/* <div className="mb-6 text-center">
        <h3 className="text-lg font-semibold text-foreground mb-2">Popular Questions</h3>
        <p className="text-sm text-muted-foreground">Click on any question to get started</p>
      </div> */}
      {/* <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full"> */}
      <div className="flex flex-row flex-wrap gap-3 justify-center">
        {starterQuestions.map((question, index) => (
          <Card
            key={question}
            className="bg-muted cursor-pointer group transition-all duration-200 hover:shadow-md hover:border-primary/30 animate-fade-in-up p-3 flex flex-row gap-2 h-full items-center justify-center"
            style={{
              animationDelay: `${index * 150}ms`,
              animationFillMode: 'backwards'
            }}
            onClick={() => handleSend(question)}
          >
            <div className="flex flex-row items-center justify-center max-w-8">
            <ArrowUpRight size={18} className="text-tint group-hover:text-primary transition-all duration-200" />
            </div>
            <p className="text-sm font-medium text-foreground leading-relaxed text-center grow">
              {question}
            </p>
          </Card>
        ))}
      </div>
    </div>
  );
};
