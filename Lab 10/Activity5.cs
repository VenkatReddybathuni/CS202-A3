using System;

namespace BasicMathApp
{
    class Calculator
    {
        private double num1;
        private double num2;

        public void GetUserInput()
        {
            while (true)
            {
                try
                {
                    Console.Write("Enter the first number: ");
                    num1 = Convert.ToDouble(Console.ReadLine());

                    Console.Write("Enter the second number: ");
                    num2 = Convert.ToDouble(Console.ReadLine());

                    break;
                }
                catch (FormatException)
                {
                    Console.WriteLine("Invalid input. Please enter numeric values only.\n");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Unexpected error: {ex.Message}\n");
                }
            }
        }

        public void PerformOperations()
        {
            double sum = num1 + num2;
            double difference = num1 - num2;
            double product = num1 * num2;

            Console.WriteLine("\nResults:");
            Console.WriteLine($"Addition: {sum}");
            Console.WriteLine($"Subtraction: {difference}");
            Console.WriteLine($"Multiplication: {product}");

            if (num2 == 0)
            {
                Console.WriteLine("Division: Cannot divide by zero.");
            }
            else
            {
                double quotient = num1 / num2;
                Console.WriteLine($"Division: {quotient}");
            }

            Console.WriteLine(sum % 2 == 0 ? "The sum is even." : "The sum is odd.");
        }
    }

    class Program
    {
        static void Main(string[] args)
        {
            Calculator calc = new Calculator();
            calc.GetUserInput();
            calc.PerformOperations();
        }
    }
}
