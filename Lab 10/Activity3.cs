using System;

namespace LoopAndFunctionDemo
{
    class LoopExamples
    {
        public void PrintNumbers1To10()
        {
            Console.WriteLine("Printing numbers from 1 to 10:");
            for (int i = 1; i <= 10; i++)
            {
                Console.Write(i + " ");
            }
            Console.WriteLine("\n");
        }

        public void StartUserInputLoop()
        {
            string input = "";
            while (input.ToLower() != "exit")
            {
                Console.Write("Enter something (or type 'exit' to quit): ");
                input = Console.ReadLine();
                if (input.ToLower() != "exit")
                {
                    Console.WriteLine("You entered: " + input);
                }
            }
            Console.WriteLine("Exited input loop.\n");
        }

        public int CalculateFactorial(int n)
        {
            if (n < 0)
            {
                Console.WriteLine("Factorial is not defined for negative numbers.");
                return -1;
            }

            int result = 1;
            for (int i = 2; i <= n; i++)
            {
                result *= i;
            }
            return result;
        }
    }

    class Program
    {
        static void Main(string[] args)
        {
            LoopExamples example = new LoopExamples();

            // 1. For loop: Print 1 to 10
            example.PrintNumbers1To10();

            // 2. While loop: User input
            example.StartUserInputLoop();

            // 3. Function: Factorial
            Console.Write("Enter a number to calculate its factorial: ");
            if (int.TryParse(Console.ReadLine(), out int number))
            {
                int factorial = example.CalculateFactorial(number);
                if (factorial != -1)
                {
                    Console.WriteLine($"Factorial of {number} is: {factorial}");
                }
            }
            else
            {
                Console.WriteLine("Invalid input. Please enter an integer.");
            }
        }
    }
}
