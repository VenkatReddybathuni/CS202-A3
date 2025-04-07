using System;

namespace StudentApp
{
    // Base Class
    class Student
    {
        public string Name { get; set; }
        public string ID { get; set; }
        public double Marks { get; set; }

        public Student(string name, string id, double marks)
        {
            Name = name;
            ID = id;
            Marks = marks;
        }

        public string GetGrade()
        {
            if (Marks >= 90) return "A";
            else if (Marks >= 75) return "B";
            else if (Marks >= 60) return "C";
            else if (Marks >= 50) return "D";
            else return "F";
        }

        public virtual void DisplayDetails()
        {
            Console.WriteLine("Student Details:");
            Console.WriteLine($"Name: {Name}");
            Console.WriteLine($"ID: {ID}");
            Console.WriteLine($"Marks: {Marks}");
            Console.WriteLine($"Grade: {GetGrade()}");
        }
    }

    // Derived Class
    class StudentIITGN : Student
    {
        public string Hostel_Name_IITGN { get; set; }

        public StudentIITGN(string name, string id, double marks, string hostelName)
            : base(name, id, marks)
        {
            Hostel_Name_IITGN = hostelName;
        }

        public override void DisplayDetails()
        {
            base.DisplayDetails();
            Console.WriteLine($"Hostel Name (IITGN): {Hostel_Name_IITGN}");
        }
    }

    class Program
    {
        static void Main(string[] args)
        {
            // Create a regular (non-IITGN) student
            Student normalStudent = new Student("Kaushal", "22110169", 72);
            normalStudent.DisplayDetails();

            Console.WriteLine(); // Spacer

            // Create an IITGN student
            StudentIITGN iitgnStudent = new StudentIITGN("Venkat", "22110220", 88, "Emiet");
            iitgnStudent.DisplayDetails();
        }
    }
}
