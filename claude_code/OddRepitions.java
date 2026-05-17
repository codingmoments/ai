import java.util.ArrayList;
import java.util.List;

public class OddRepitions {
  public static void main(String[] args) {
    int[] numbers = { 1, 2, 3, 2, 1, 3, 4, 1 };
    List<Integer> results = findOddRepitions(numbers);
    System.out.println("The number that appears an odd number of times is: " + results);
  }

  public static List<Integer> findOddRepitions(int[] arr) {
    List<Integer> oddRepitions = new ArrayList<>();
    for (int i = 0; i < arr.length; i++) {
      int count = 0;
      for (int j = 0; j < arr.length; j++) {
        if (arr[i] == arr[j]) {
          count++;
        }
      }
      if (count % 2 != 0 && !oddRepitions.contains(arr[i])) {
        oddRepitions.add(arr[i]);
      }
    }
    return oddRepitions;
  }
}