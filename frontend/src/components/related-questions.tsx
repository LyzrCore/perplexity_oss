import { PlusIcon } from "lucide-react";
import { memo } from "react";

interface RelatedQuestionsProps {
  /** Array of related questions to display */
  questions: string[];
  /** Callback when a question is selected */
  onSelect: (question: string) => void;
}

/**
 * Component for displaying related questions that users can click to ask
 */
function RelatedQuestions({ questions, onSelect }: RelatedQuestionsProps) {
  return (
    <div className="divide-y border-t mt-2">
      {questions.map((question, index) => (
        <div
          key={`question-${index}`}
          className="flex cursor-pointer items-center py-2 font-medium justify-between "
          onClick={() => onSelect(question)}
        >
          <span>{question.toLowerCase()}</span>
          <PlusIcon className="text-tint mr-2" size={20} />
        </div>
      ))}
    </div>
  );
}

export default memo(RelatedQuestions);
