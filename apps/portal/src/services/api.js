/**
 * Fake "API": reads local JSON files and returns Promises with an artificial delay,
 * imitating the behavior of a real backend (loading state, asynchronous calls).
 */
import patients from '../data/patients.json';
import doctors from '../data/doctors.json';

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export async function getPatients() {
  await wait(700);
  return structuredClone(patients);
}

export async function getDoctors() {
  await wait(300);
  return structuredClone(doctors);
}
